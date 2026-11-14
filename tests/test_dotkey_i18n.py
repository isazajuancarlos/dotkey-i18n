# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Juan Carlos Isaza

"""Tests de dotkey-i18n. Sin dependencias. Usa fixtures JSON en un tmp_path."""
import json

import pytest

from dotkey_i18n import Translator


@pytest.fixture
def locales(tmp_path):
    (tmp_path / "es.json").write_text(json.dumps({
        "login": {"welcome": "Hola, {name}", "submit": "Entrar"},
        "menu": {"reports": "Informes", "settings": "Ajustes"},
        "plain": "texto sin formato",
    }), encoding="utf-8")
    (tmp_path / "en.json").write_text(json.dumps({
        "login": {"welcome": "Hello, {name}", "submit": "Sign in"},
        "menu": {"reports": "Reports"},   # a propósito SIN menu.settings
    }), encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------------------
# Notación de punto e interpolación
# ---------------------------------------------------------------------------
def test_navega_claves_con_punto(locales):
    tr = Translator(locales, default_lang="es")
    assert tr.t("menu.reports") == "Informes"
    assert tr.t("login.submit") == "Entrar"


def test_interpolacion(locales):
    tr = Translator(locales, default_lang="es")
    assert tr.t("login.welcome", name="Juan") == "Hola, Juan"


def test_sin_kwargs_devuelve_literal(locales):
    tr = Translator(locales, default_lang="es")
    assert tr.t("plain") == "texto sin formato"


def test_interpolacion_faltante_no_revienta(locales):
    # falta {name}: devuelve el texto crudo en vez de lanzar KeyError
    tr = Translator(locales, default_lang="es")
    assert tr.t("login.welcome") == "Hola, {name}"


def test_call_es_alias_de_t(locales):
    tr = Translator(locales, default_lang="es")
    assert tr("menu.reports") == tr.t("menu.reports")


# ---------------------------------------------------------------------------
# Selección de idioma
# ---------------------------------------------------------------------------
def test_lang_explicito(locales):
    tr = Translator(locales, default_lang="es")
    assert tr.t("login.submit", lang="en") == "Sign in"


def test_lang_getter(locales):
    actual = {"v": "en"}
    tr = Translator(locales, default_lang="es", lang_getter=lambda: actual["v"])
    assert tr.t("login.submit") == "Sign in"
    actual["v"] = "es"
    assert tr.t("login.submit") == "Entrar"


def test_lang_getter_que_falla_cae_a_default(locales):
    def roto():
        raise RuntimeError("sin sesión")
    tr = Translator(locales, default_lang="es", lang_getter=roto)
    assert tr.t("login.submit") == "Entrar"


def test_lang_getter_vacio_cae_a_default(locales):
    tr = Translator(locales, default_lang="es", lang_getter=lambda: None)
    assert tr.t("login.submit") == "Entrar"


# ---------------------------------------------------------------------------
# Fallback al idioma por defecto (lo que le faltaba al original)
# ---------------------------------------------------------------------------
def test_fallback_al_default_si_falta_en_el_idioma(locales):
    # menu.settings existe en es pero NO en en; con default es, cae a es
    tr = Translator(locales, default_lang="es")
    assert tr.t("menu.settings", lang="en") == "Ajustes"


def test_fallback_desactivado_devuelve_la_clave(locales):
    tr = Translator(locales, default_lang="es", fallback_to_default=False)
    assert tr.t("menu.settings", lang="en") == "menu.settings"


# ---------------------------------------------------------------------------
# Clave ausente / on_missing
# ---------------------------------------------------------------------------
def test_clave_ausente_devuelve_la_clave(locales):
    tr = Translator(locales, default_lang="es")
    assert tr.t("no.existe") == "no.existe"


def test_clave_a_un_dict_no_es_texto_devuelve_la_clave(locales):
    # 'menu' es un dict, no una hoja de texto
    tr = Translator(locales, default_lang="es")
    assert tr.t("menu") == "menu"


def test_on_missing_personalizado(locales):
    marcas = []
    tr = Translator(locales, default_lang="es",
                    on_missing=lambda k, l: marcas.append((k, l)) or f"⟨{k}⟩")
    assert tr.t("no.existe", lang="es") == "⟨no.existe⟩"
    assert marcas == [("no.existe", "es")]


# ---------------------------------------------------------------------------
# Idioma inexistente, available_langs, reload
# ---------------------------------------------------------------------------
def test_idioma_sin_fichero(locales):
    tr = Translator(locales, default_lang="es")
    # 'fr' no tiene fichero; sin fallback (default también es 'fr'-inexistente
    # no aplica), cae a on_missing -> la clave
    assert tr.t("menu.reports", lang="fr") == "Informes"  # cae a default es


def test_available_langs(locales):
    tr = Translator(locales, default_lang="es")
    assert tr.available_langs == ["en", "es"]


def test_available_langs_dir_inexistente(tmp_path):
    tr = Translator(tmp_path / "no_existe", default_lang="es")
    assert tr.available_langs == []


def test_reload_relee_del_disco(locales):
    tr = Translator(locales, default_lang="es")
    assert tr.t("menu.reports") == "Informes"
    # edita el fichero en caliente
    (locales / "es.json").write_text(json.dumps({"menu": {"reports": "CAMBIADO"}}),
                                     encoding="utf-8")
    assert tr.t("menu.reports") == "Informes"   # cache: aún el viejo
    tr.reload()
    assert tr.t("menu.reports") == "CAMBIADO"    # tras reload, el nuevo


def test_json_invalido_no_revienta(tmp_path):
    (tmp_path / "es.json").write_text("{ esto no es json", encoding="utf-8")
    tr = Translator(tmp_path, default_lang="es")
    assert tr.t("cualquier.cosa") == "cualquier.cosa"   # dict vacío -> la clave
