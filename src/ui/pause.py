"""Duraklatma menusu.

Oyunun **ustune biner**: altaki sahne cizilmeye devam eder ama guncellenmez.
Arka plan karartilir ve hafif bulaniklastirilir (4x kucult, 4x buyut -
Gaussian gerekmez).

**Kritik UX (docs/menu-ui.md 7):** ANA MENU'ye basinca kaydedildigi
*acikca* yazilir. "Kaydedilmemis ilerleme" belirsizligi oyuncuda soru
firtinasi yaratir: Kaydetmedi mi? O boss dovusunu tekrar mi oynayacagim?
Bu tuzaga dusmuyoruz.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.core.input import Action
from src.core.scene import Scene
from src.systems.save import read_save, write_save
from src.ui import text
from src.ui.i18n import t
from src.ui.widgets import Menu, MenuItem, blur, panel

PANEL_WIDTH = 168
# Bes oge + ANA MENU oncesindeki bosluk. Kisa tutunca son satir cerceveyi
# kesiyordu - panel yuksekligi menu icerigiyle birlikte hesaplanmali.
# YETENEKLER eklenince (25.09.2026) bir satir (18) buyudu.
PANEL_HEIGHT = 146
MENU_Y = INTERNAL_HEIGHT // 2 - 38
BLUR_FACTOR = 4


class PauseScene(Scene):
    blocks_update = True        # Altaki oyun donar
    blocks_draw = False         # ...ama gorunur kalir
    transparent_bg = True

    def on_enter(self, save_data=None, **kwargs: object) -> None:
        self.save_data = save_data
        self.confirm_quit: Menu | None = None
        self.saved_notice = 0
        self._save_succeeded = False
        self._blurred: pygame.Surface | None = None

        self.menu = Menu([
            MenuItem("pause.resume", self._resume),
            MenuItem("pause.equipment", self._open_equipment),
            MenuItem("pause.skills", self._open_skills),
            MenuItem("pause.settings", self._open_settings),
            MenuItem("pause.main_menu", self._ask_quit, gap_before=True),
        ], INTERNAL_WIDTH // 2, MENU_Y, width=120,
            centered=True, on_sound=self.game.play_sound)

    # --- Eylemler -----------------------------------------------------------
    def _open_equipment(self) -> None:
        """Silah degistirme ekrani.

        Bu girdi bir donem KAPALIYDI ve ipucu olarak "Bolum 2'de acilir"
        diyordu - ama Bolum 2'de bir sey acilmiyordu. Arayuzun tutamadigi
        soz, olum yazisinin "R ile sifirla" deyip R'nin hicbir yerde
        dinlenmemesiyle ayni sinif hataydi (Arda iki hatayi da canli
        oynanista buldu).
        """
        from src.scenes.play import PlayScene
        from src.ui.equipment import EquipmentScene
        # Oyuncuyu yigindan `find` ile aliyoruz: silah degisiminin
        # **aninda** etkili olmasi icin canli `Player` nesnesi gerekiyor.
        # Yalnizca kayda yazmak, duraklatmadan cikinca eski silahla
        # devam etmek demekti.
        play = self.scenes.find(PlayScene)
        self.scenes.push(EquipmentScene, save_data=self.save_data,
                         player=getattr(play, "player", None))

    def _open_skills(self) -> None:
        """Yetenek agaci - her yerden (Arda 25.09.2026).

        Eskiden yalnizca B4'un kampinda aciliyordu: puan kazanilsa bile
        baska yerde harcanamiyordu. Canli sahne veriliyor ki acilan dugum
        (can, pencere, hareket) duraklatmadan cikinca HEMEN hissedilsin.
        """
        from src.scenes.play import PlayScene
        from src.systems import skilltree
        from src.ui.skill_tree import SkillTreeScene
        self.scenes.push(SkillTreeScene, save_data=self.save_data,
                         tree=skilltree, play=self.scenes.find(PlayScene))

    def _resume(self) -> None:
        self.scenes.pop()

    def _open_settings(self) -> None:
        from src.ui.settings_scene import SettingsScene
        self.scenes.push(SettingsScene)

    def _ask_quit(self) -> None:
        # Once kaydet, sonra sor. Oyuncu "kaydedildi" yazisini gordugunde
        # bu gercekten olmus olmali.
        self._save_succeeded = self._save_progress()
        self.confirm_quit = Menu([
            MenuItem("common.cancel", self._cancel_quit),
            MenuItem("pause.quit_confirm", self._to_main_menu, danger=True,
                     enabled=self._save_succeeded),
        ], INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2 + 18, width=140,
            centered=True, on_sound=self.game.play_sound)

    def _cancel_quit(self) -> None:
        self.confirm_quit = None

    def _save_progress(self) -> bool:
        data = self.save_data
        if data is None:
            data, _ = read_save()
        self.saved_notice = 0
        if data is None or not write_save(data):
            return False
        self.saved_notice = 180
        self.game.play_sound("save_written")
        return True

    def _to_main_menu(self) -> None:
        # Yazma basarisizsa canli ilerlemeyi terk etme; IPTAL ile
        # oyuna donup ANA MENU'yu yeniden secmek yazmayi tekrar dener.
        if not self._save_succeeded:
            return
        from src.ui.menu import MainMenuScene
        self.scenes.set_root(MainMenuScene)

    # --- Dongu --------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if self.game.input.pressed(Action.CANCEL):
                if self.confirm_quit:
                    self._cancel_quit()
                else:
                    self._resume()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            (self.confirm_quit or self.menu).click(self.game)

    def update(self) -> None:
        self.saved_notice = max(0, self.saved_notice - 1)
        (self.confirm_quit or self.menu).update(self.game)

    def draw(self, surface: pygame.Surface) -> None:
        self._draw_backdrop(surface)

        rect = pygame.Rect(INTERNAL_WIDTH // 2 - PANEL_WIDTH // 2,
                           INTERNAL_HEIGHT // 2 - PANEL_HEIGHT // 2 - 6,
                           PANEL_WIDTH, PANEL_HEIGHT)
        panel(surface, rect)
        text.draw(surface, t("pause.heading"), INTERNAL_WIDTH // 2,
                  rect.y + 8, color=palette.role("ui_text"), align="center",
                  tracking=2)

        self.menu.draw(surface)
        self._draw_status(surface)

        if self.confirm_quit:
            self._draw_quit_dialog(surface)

        (self.confirm_quit or self.menu).draw_cursor(surface, self.game)

    # --- Cizim yardimcilari -------------------------------------------------
    def _draw_backdrop(self, surface: pygame.Surface) -> None:
        """Oyun arkada gorunur ama karartilmis ve bulanik."""
        if self._blurred is None:
            self._blurred = blur(surface.copy(), BLUR_FACTOR)
        surface.blit(self._blurred, (0, 0))

        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        veil.fill((*palette.color("void"), 150))
        surface.blit(veil, (0, 0))

    def _draw_status(self, surface: pygame.Surface) -> None:
        data = self.save_data
        if data is None:
            return
        dots = "●" * (data.echo_tier + 1) + "○" * (2 - data.echo_tier)
        info = t("pause.status", chapter=data.chapter, dots=dots, gold=data.gold)
        text.draw(surface, info, INTERNAL_WIDTH // 2, INTERNAL_HEIGHT - 30,
                  color=palette.role("ui_text_dim"), align="center")
        # Harcanmamis puan varsa bir satir: oyuncu YETENEKLER'e bakmasi
        # gerektigini menuye girer girmez gorsun.
        from src.systems import skilltree
        points = skilltree.available_points(data)
        if points > 0:
            text.draw(surface, t("pause.skill_points", count=points),
                      INTERNAL_WIDTH // 2, INTERNAL_HEIGHT - 44,
                      color=palette.color("gold"), align="center")

    def _draw_quit_dialog(self, surface: pygame.Surface) -> None:
        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        veil.fill((*palette.color("void"), 190))
        surface.blit(veil, (0, 0))

        rect = pygame.Rect(INTERNAL_WIDTH // 2 - 100,
                           INTERNAL_HEIGHT // 2 - 40, 200, 80)
        panel(surface, rect)
        text.draw(surface, t("pause.quit_question"), INTERNAL_WIDTH // 2, rect.y + 10,
                  color=palette.role("ui_text"), align="center")
        notice = (t("pause.quit_saved") if self._save_succeeded
                  else t("pause.quit_failed"))
        color = "echo_bright" if self._save_succeeded else "danger_bright"
        text.draw(surface, notice, INTERNAL_WIDTH // 2,
                  rect.y + 24, color=palette.color(color),
                  align="center")
        self.confirm_quit.draw(surface)

    def debug_lines(self) -> list[str]:
        return [f"duraklatma · seçili: {self.menu.selected.text}"]
