#!/usr/bin/env python3
"""
Memory Consolidator — ASTOR Workspace
Se ejecuta en SessionStart via hook en .claude/settings.json

Flujo:
  1. Lee el .jsonl de la sesión anterior (ya cerrada)
  2. Procesa archivos nuevos en memory/inbox/
  3. Llama a Claude Haiku 4.5 para extraer lo relevante
  4. Actualiza los archivos en memory/
"""
import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime

# Agregar el directorio del script al path para imports relativos
sys.path.insert(0, str(Path(__file__).parent))


def get_api_key() -> str | None:
    """Carga la API key desde .env en la raíz del workspace."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip().strip("\"'")
    return os.environ.get("ANTHROPIC_API_KEY")


def get_memory_dir() -> Path | None:
    """
    Resuelve el path al directorio memory/ del proyecto.
    Prioridad:
      1. CLAUDE_PROJECT_DIR env var (inyectada por Claude Code al hook)
      2. Búsqueda por convención en ~/.claude/projects/
    """
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project_dir:
        # Convertir path a key de directorio de proyecto
        # Ejemplo: C:\Users\Usuario\Desktop\espacio... → C--Users-Usuario-Desktop-espacio...
        safe = (
            project_dir
            .replace("\\", "-")
            .replace("/", "-")
            .replace(":", "")
        )
        base = Path.home() / ".claude" / "projects" / safe / "memory"
        if base.exists():
            return base

    # Fallback: buscar en todos los proyectos cuál tiene MEMORY.md
    known = Path.home() / ".claude" / "projects"
    if not known.exists():
        return None
    for d in known.iterdir():
        if not d.is_dir():
            continue
        mem = d / "memory" / "MEMORY.md"
        if mem.exists():
            return d / "memory"

    return None


def get_log_path() -> Path:
    """Retorna el path al archivo de log de procesamiento."""
    return Path(__file__).parent.parent.parent / "memory" / "processed_log.json"


# --- Logging persistente del consolidador (memory/consolidator.log) ---

LOG_MAX_BYTES = 1_048_576  # 1 MB — al superarlo se rota a consolidator.log.1


def get_consolidator_log_path() -> Path:
    """Retorna el path al log de ejecución del consolidador (misma base que processed_log.json)."""
    return Path(__file__).parent.parent.parent / "memory" / "consolidator.log"


def _rotate_log_if_needed(log_path: Path) -> None:
    """
    Rotación simple por tamaño: si el log supera LOG_MAX_BYTES, lo renombra a
    consolidator.log.1 (sobrescribiendo el backup previo) y reinicia el log.
    Nunca lanza — un fallo de rotación no debe romper el consolidador.
    """
    try:
        if log_path.exists() and log_path.stat().st_size >= LOG_MAX_BYTES:
            backup = log_path.with_suffix(log_path.suffix + ".1")
            if backup.exists():
                backup.unlink()
            log_path.rename(backup)
    except Exception:
        pass


def log_line(msg: str) -> None:
    """
    Escribe una línea con timestamp en memory/consolidator.log.
    Rota por tamaño antes de escribir. Silencia cualquier error de I/O:
    el logging NUNCA debe bloquear el arranque de sesión.
    """
    try:
        log_path = get_consolidator_log_path()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        _rotate_log_if_needed(log_path)
        stamp = datetime.now().isoformat(timespec="seconds")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{stamp}] {msg}\n")
    except Exception:
        pass


def _report(msg: str) -> None:
    """Emite a stdout (debug manual) y al log persistente."""
    print(msg)
    log_line(msg)


def load_log() -> dict:
    """Carga el registro de archivos ya procesados."""
    log_path = get_log_path()
    if log_path.exists():
        try:
            return json.loads(log_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"processed_jsonl": [], "processed_files": [], "last_run": None}


def save_log(log_data: dict) -> None:
    """Guarda el registro de archivos procesados."""
    log_path = get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        json.dumps(log_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def file_hash(path: Path) -> str:
    """Calcula el hash MD5 de un archivo para deduplicación."""
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()
    except Exception:
        return str(path.stat().st_size)


def main() -> None:
    _report("[Consolidador] Iniciando...")

    # 1. Validar prerequisitos
    api_key = get_api_key()  # Opcional: se usa si está disponible, si no usa claude CLI

    memory_dir = get_memory_dir()
    if not memory_dir:
        _report("[Consolidador] No se encontró directorio memory/ — saltando")
        return

    _report(f"[Consolidador] memory/ → {memory_dir}")

    log = load_log()
    changed = False          # True si se escribió algo en memory/ (contexto)
    session_extracted = False # True si hubo extracción real (alimenta skill-evolution)
    log_dirty = False         # True si processed_log debe persistirse (aunque no haya extracción)

    # 2. Procesar .jsonl de la sesión anterior
    try:
        from jsonl_processor import find_previous_jsonl, extract_relevant_fragments
        from memory_writer import update_memory_from_jsonl, update_memory_from_file

        current_session_id = os.environ.get("CLAUDE_SESSION_ID", "")
        projects_dir = Path.home() / ".claude" / "projects"

        session_data = find_previous_jsonl(
            current_session_id=current_session_id,
            projects_dir=projects_dir,
        )

        if session_data:
            session_path = session_data["session_path"]
            if session_path not in log["processed_jsonl"]:
                _report(f"[Consolidador] Procesando sesión: {session_data['session_date']}")

                # Marcar la sesión como procesada SIEMPRE: procesar un .jsonl es un
                # resultado terminal aunque la extracción sea {} o falle. Así el log
                # avanza y no se reintenta la misma sesión en cada arranque.
                extracted_data = {}
                try:
                    fragments = extract_relevant_fragments(session_path)
                    if fragments and len(fragments.strip()) > 50:
                        extracted_data = update_memory_from_jsonl(fragments, memory_dir, api_key)
                        if extracted_data:
                            changed = True
                            from skill_evolver import store_extraction
                            log = store_extraction(log, extracted_data)
                            session_extracted = True
                            _report("[Consolidador] ✓ Sesión anterior procesada (con extracción)")
                        else:
                            _report("[Consolidador] Sesión anterior procesada — sin contenido relevante ({})")
                    else:
                        _report("[Consolidador] Sesión anterior procesada — fragmentos insuficientes")
                except Exception as e:
                    # Fallo parcial: igual marcamos la sesión como procesada (terminal).
                    _report(f"[Consolidador] Error extrayendo de la sesión (se marca procesada igual): {e}")

                # Persistir el avance pase lo que pase con la extracción.
                log["processed_jsonl"].append(session_path)
                log["processed_jsonl"] = log["processed_jsonl"][-20:]  # cap histórico existente
                log_dirty = True
            else:
                _report("[Consolidador] Sesión anterior ya procesada — saltando")
        else:
            _report("[Consolidador] Sin sesión anterior para procesar")

    except Exception as e:
        _report(f"[Consolidador] Error procesando sesión: {e}")

    # 3. Procesar archivos en inbox/
    inbox_dir = Path(__file__).parent.parent.parent / "memory" / "inbox"
    if inbox_dir.exists():
        try:
            from doc_processor import extract_text

            inbox_files = [f for f in inbox_dir.iterdir() if not f.name.startswith(".")]

            if not inbox_files:
                _report("[Consolidador] inbox/ vacío")
            else:
                for file_path in inbox_files:
                    fhash = file_hash(file_path)
                    if fhash in log["processed_files"]:
                        _report(f"[Consolidador] {file_path.name} ya procesado — saltando")
                        continue

                    _report(f"[Consolidador] Procesando inbox: {file_path.name}")
                    try:
                        file_data = extract_text(file_path)
                        if file_data:
                            update_memory_from_file(file_data, memory_dir, api_key)
                            log["processed_files"].append(fhash)
                            changed = True
                            log_dirty = True
                            _report(f"[Consolidador] ✓ {file_path.name} procesado")
                        else:
                            _report(f"[Consolidador] {file_path.name}: formato no soportado")
                    except Exception as e:
                        _report(f"[Consolidador] Error procesando {file_path.name}: {e}")

        except Exception as e:
            _report(f"[Consolidador] Error procesando inbox/: {e}")
    else:
        _report("[Consolidador] inbox/ no encontrado")

    # 4. Skill evolution (si se procesó una sesión nueva con extracción)
    if session_extracted:
        try:
            from skill_evolver import maybe_evolve_skills
            _, log = maybe_evolve_skills(
                log=log,
                api_key=api_key,
                recent_extractions=log.get("recent_extractions", []),
            )
        except Exception as e:
            _report(f"[Consolidador] Error en skill evolution (no crítico): {e}")

    # 5. Guardar log y reportar
    #    Persistir SIEMPRE que haya habido avance registrable (extracción, escritura
    #    en memory/, o simplemente una sesión marcada como procesada). Así last_run
    #    avanza aunque la extracción devuelva {} o falle parcialmente.
    if changed or session_extracted or log_dirty:
        log["last_run"] = datetime.now().isoformat()
        save_log(log)
        if changed:
            _report(f"[Consolidador] ✓ memory/ actualizado — RESULTADO: log persistido, last_run={log['last_run']}")
        else:
            _report(f"[Consolidador] ✓ log persistido (sin escritura en memory/) — last_run={log['last_run']}")
    else:
        _report("[Consolidador] Sin cambios nuevos — memory/ y log sin modificar")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # NUNCA bloquear el inicio de sesión
        _report(f"[Consolidador] Error (no crítico): {e}")
    finally:
        sys.exit(0)
