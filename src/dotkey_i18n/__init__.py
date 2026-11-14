# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Juan Carlos Isaza

"""dotkey-i18n — internacionalización mínima: claves con notación de punto sobre
ficheros JSON, con caché, fallback e interpolación. Sin dependencias.

    # es.json -> {"login": {"welcome": "Hola, {name}"}}
    from dotkey_i18n import Translator

    tr = Translator("locales", default_lang="es")
    tr.t("login.welcome", name="Juan")     # "Hola, Juan"
    tr.t("login.welcome", lang="en", name="Juan")

No arrastra gettext, ni ficheros .po, ni un paso de compilación: tus traducciones
son JSON que cualquiera puede editar. Pensada para apps pequeñas y medianas que
solo quieren un ``t()`` honesto.

Nació del servicio i18n de un sistema de gestión de informes (ES/EN), extraído y
desacoplado del framework: el idioma actual entra por un ``lang_getter``
inyectable, así funciona igual con NiceGUI, Flask, FastAPI o un script.
"""
from __future__ import annotations

import json
from pathlib import Path

__all__ = ["Translator", "__version__"]

__version__ = "0.1.1"


class Translator:
    """Carga traducciones JSON por idioma y resuelve claves con notación de punto.

    Cada idioma es un fichero ``<lang>.json`` en ``directory`` con un dict
    (anidable). ``t("a.b.c")`` navega ``a`` → ``b`` → ``c``.

    :param directory: carpeta con los ``<lang>.json``.
    :param default_lang: idioma por defecto y de *fallback*.
    :param lang_getter: invocable sin argumentos que devuelve el idioma actual
        (p.ej. leer la sesión del usuario). Si es ``None``, se usa
        ``default_lang`` salvo que pases ``lang=`` a :meth:`t`.
    :param fallback_to_default: si una clave falta en el idioma pedido, buscarla
        en ``default_lang`` antes de rendirse.
    :param on_missing: invocable ``(key, lang) -> str`` para cuando la clave no
        existe en ningún sitio. Por defecto devuelve la propia clave (fallback
        visible, nunca revienta la UI).
    """

    def __init__(self, directory, *, default_lang="en", lang_getter=None,
                 fallback_to_default=True, on_missing=None):
        self.directory = Path(directory)
        self.default_lang = default_lang
        self.lang_getter = lang_getter
        self.fallback_to_default = fallback_to_default
        self.on_missing = on_missing or (lambda key, lang: key)
        self._cache: dict[str, dict] = {}

    def _load(self, lang: str) -> dict:
        if lang not in self._cache:
            path = self.directory / f"{lang}.json"
            try:
                self._cache[lang] = json.loads(path.read_text("utf-8"))
            except (OSError, ValueError):
                self._cache[lang] = {}
        return self._cache[lang]

    def _lookup(self, strings: dict, key: str):
        """Navega la clave con notación de punto; None si falta o no es texto."""
        value = strings
        for part in key.split("."):
            if not isinstance(value, dict):
                return None
            value = value.get(part)
            if value is None:
                return None
        return value if isinstance(value, str) else None

    def _resolver_idioma(self, lang):
        if lang is not None:
            return lang
        if self.lang_getter is not None:
            try:
                got = self.lang_getter()
                if got:
                    return got
            except Exception:
                pass
        return self.default_lang

    def t(self, key: str, *, lang=None, **kwargs) -> str:
        """Traduce ``key`` (notación de punto) al idioma actual.

        Resolución del idioma: ``lang`` explícito → ``lang_getter()`` →
        ``default_lang``. Si la clave falta en ese idioma y
        ``fallback_to_default`` está activo, se reintenta en ``default_lang``.
        Si sigue sin encontrarse, se llama a ``on_missing`` (por defecto,
        devuelve la clave). ``**kwargs`` se interpolan con ``str.format``; si la
        interpolación falla, se devuelve el texto sin formatear.
        """
        idioma = self._resolver_idioma(lang)

        value = self._lookup(self._load(idioma), key)
        if value is None and self.fallback_to_default and idioma != self.default_lang:
            value = self._lookup(self._load(self.default_lang), key)
        if value is None:
            return self.on_missing(key, idioma)

        if not kwargs:
            return value
        try:
            return value.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return value

    def __call__(self, key: str, *, lang=None, **kwargs) -> str:
        """Azúcar: ``tr("clave")`` equivale a ``tr.t("clave")``."""
        return self.t(key, lang=lang, **kwargs)

    @property
    def available_langs(self):
        """Idiomas con fichero ``<lang>.json`` presente en la carpeta."""
        if not self.directory.is_dir():
            return []
        return sorted(p.stem for p in self.directory.glob("*.json"))

    def reload(self):
        """Vacía la caché para releer los JSON del disco (tras editarlos)."""
        self._cache.clear()
