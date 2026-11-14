# dotkey-i18n

Internacionalización mínima para Python: **claves con notación de punto** sobre
ficheros **JSON**, con caché, *fallback* e interpolación. Sin dependencias, sin
gettext, sin ficheros `.po`, sin paso de compilación.

```python
from dotkey_i18n import Translator

tr = Translator("locales", default_lang="es")

tr.t("login.welcome", name="Juan")            # "Hola, Juan"
tr.t("menu.reports", lang="en")               # "Reports"
```

Tus traducciones son JSON que cualquiera puede editar:

```json
// locales/es.json
{
  "login": { "welcome": "Hola, {name}", "submit": "Entrar" },
  "menu":  { "reports": "Informes", "settings": "Ajustes" }
}
```

## Instalación

```bash
pip install dotkey-i18n
```

Sin dependencias. Requiere Python ≥ 3.9.

## Por qué existe

`gettext` y Babel son potentes, pero para una app pequeña o mediana pagas un
peaje: ficheros `.po`, un paso de compilación (`.mo`), y herramientas aparte. A
veces solo quieres un `t()` honesto sobre unos JSON. Eso es esto.

## Qué hace bien

**Notación de punto.** `t("login.submit")` navega `login` → `submit` en el JSON
anidado. Agrupa las cadenas por pantalla o por módulo sin claves planas
kilométricas.

**Fallback al idioma por defecto.** Si una clave falta en el idioma pedido, se
busca en `default_lang` antes de rendirse. Tus traducciones pueden ir
incompletas sin dejar huecos en blanco:

```python
tr = Translator("locales", default_lang="es")
tr.t("menu.settings", lang="en")   # no está en en.json -> cae a es.json
```

**Nunca revienta la UI.** Clave que no existe → devuelve la propia clave (un
marcador visible, no una excepción). Interpolación con un `{campo}` que falta →
devuelve el texto sin formatear. JSON corrupto → se trata como vacío. Puedes
personalizar el caso "clave ausente" con `on_missing`.

**Agnóstico del framework.** El idioma actual entra por un `lang_getter`
inyectable, así funciona igual con NiceGUI, Flask, FastAPI o un script suelto:

```python
# NiceGUI: idioma desde la sesión del usuario
tr = Translator("locales", default_lang="es",
                lang_getter=lambda: app.storage.user.get("idioma"))

# Flask
tr = Translator("locales", lang_getter=lambda: session.get("lang"))
```

Prioridad: `lang=` explícito → `lang_getter()` → `default_lang`.

## API

```python
tr = Translator(
    directory,                 # carpeta con los <lang>.json
    default_lang="en",         # idioma por defecto y de fallback
    lang_getter=None,          # callable() -> idioma actual
    fallback_to_default=True,  # buscar en default_lang si falta la clave
    on_missing=None,           # callable(key, lang) -> str para claves ausentes
)

tr.t("a.b.c", lang=None, **kwargs)   # traducir (o tr("a.b.c"))
tr.available_langs                    # ["en", "es", ...] según los ficheros
tr.reload()                           # releer los JSON tras editarlos
```

## De dónde viene

Salió del servicio i18n de un sistema de gestión de informes (español/inglés).
Estaba atado al framework —leía el idioma de la sesión de NiceGUI directamente—;
al extraerlo se desacopló con el `lang_getter`, y se le añadió el fallback al
idioma por defecto que el original no tenía.

## Tests

```bash
pip install "dotkey-i18n[test]"
pytest
```

19 tests: notación de punto, interpolación, selección de idioma, fallback, claves
ausentes, `reload` y JSON corrupto. Verificados por mutación.

## Licencia

Apache-2.0.
