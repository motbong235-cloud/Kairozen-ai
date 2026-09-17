# -*- coding: utf-8 -*-
"""Kairozen AI — Projects + templates (Website / Bot / API / Admin) + Grok"""
import os, re, json, time, uuid, threading
from pathlib import Path
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder=".", static_url_path="")

GROK_API_KEY = os.environ.get("GROK_API_KEY", os.environ.get("XAI_API_KEY", ""))
GROK_API_URL = os.environ.get("GROK_API_URL", "https://api.x.ai/v1/chat/completions")
GROK_MODEL = os.environ.get("GROK_MODEL", "grok-3")
DATA_DIR = Path(os.environ.get("DATA_DIR", "./data"))
PROJECTS_DIR = DATA_DIR / "projects"
_lock = threading.RLock()

SYSTEM_BASE = (
    "អ្នកជា Kairozen AI — ជំនួយការ AI របស់ Kairozen។ "
    "ឆ្លើយជាភាសាខ្មែរជានិច្ច លុះតែអ្នកប្រើសុំភាសាផ្សេង។ "
    "ជួយតែការងារស្របច្បាប់៖ Website, Telegram/Discord bot, API, UI, "
    "automation ក្នុងប្រព័ន្ធរបស់អ្នកប្រើ, រៀន programming, "
    "security ជាគោលការណ៍, admin/monitoring ផ្ទាល់ខ្លួន។ "
    "បដិសេធ៖ hacking, exploit, phishing, malware, ចូលប្រព័ន្ធគេដោយគ្មានសិទ្ធិ, "
    "carding, scam tools។ "
    "ពេលសុំ code ប្រើ fence ```path/file.ext សម្រាប់រាល់ file។"
)

PROJECT_EXTRA = (
    "\nអ្នកកំពុងធ្វើគម្រោងធំ។ រក្សា consistency នៃ file/API/UI។ "
    "បែងចែកជំហានបើ task ធំ។ បន្ថែម README និង .env.example ពេលសមស្រប។"
)

TEMPLATES = {
    "website": {
        "title": "Website",
        "description": "Landing / ហាង / dashboard ជា HTML+CSS+JS ឬ Flask",
        "starter": (
            "បង្កើតគម្រោង website ទំនើប៖\n"
            "1) index.html responsive\n2) style.css\n3) app.js មូលដ្ឋាន\n"
            "4) README.md របៀបបើក\nរចនាងងឹត premium, ភាសាខ្មែរ។"
        ),
    },
    "bot": {
        "title": "Telegram Bot",
        "description": "Bot ធម្មតា pyTelegramBotAPI — ម៉ឺនុយ, admin, webhook/polling",
        "starter": (
            "បង្កើត Telegram bot Python៖\n"
            "bot.py, requirements.txt, README.md, .env.example\n"
            "មុខងារ៖ /start, ម៉ឺនុយខ្មែរ, admin check តាម ADMIN_ID។"
        ),
    },
    "api": {
        "title": "REST API",
        "description": "Flask/FastAPI — endpoints, auth key, health",
        "starter": (
            "បង្កើត REST API Flask៖\n"
            "app.py, requirements.txt, README.md\n"
            "Endpoints: GET /health, GET /api/items, POST /api/items\n"
            "API key តាម header X-API-Key។"
        ),
    },
    "admin": {
        "title": "Admin / Monitoring",
        "description": "Dashboard មើល health, log សង្ខេប, stats ប្រព័ន្ធផ្ទាល់ខ្លួន",
        "starter": (
            "បង្កើត admin monitoring សម្រាប់ server ផ្ទាល់ខ្លួន៖\n"
            "app.py + dashboard HTML\n"
            "បង្ហាញ: uptime, health, ចំនួន request សាមញ្ញ (in-memory)\n"
            "គ្មានការស្កេន network គេ — តែ app ផ្ទាល់ខ្លួន។"
        ),
    },
}

SECURITY_GUIDE = {
    "title": "គោលការណ៍ Security (មិនមែន attack)",
    "points": [
        "រក្សា API key / BOT_TOKEN ក្នុង Environment Variables — មិនដាក់ក្នុង Git",
        "ប្រើ HTTPS នៅ production",
        "Validate input ពី user (ប្រវែង, ប្រភេទ) មុនពេលប្រើ",
        "កំណត់ rate limit លើ API សាធារណៈ",
        "បំបែក ADMIN_ID / សិទ្ធិ admin ច្បាស់",
        "Backup DATA_DIR និងប្រើ persistent disk លើ Render",
        "Update dependencies ជាប្រចាំ (pip)",
        "កុំ log password ឬ token ពេញ",
        "CORS កំណត់ domain ពេលត្រូវការ",
        "គោលការណ៍ least privilege — service account តែសិទ្ធិចាំបាច់",
    ],
}


def _ensure_dirs():
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

def _proj_path(pid: str) -> Path:
    safe = re.sub(r"[^a-zA-Z0-9_-]", "", pid)[:64]
    return PROJECTS_DIR / f"{safe}.json"

def _load_project(pid: str):
    path = _proj_path(pid)
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _save_project(proj: dict):
    _ensure_dirs()
    path = _proj_path(proj["id"])
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(proj, f, ensure_ascii=False, indent=2)
    tmp.replace(path)

def _list_projects():
    _ensure_dirs()
    items = []
    for p in sorted(PROJECTS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            with p.open("r", encoding="utf-8") as f:
                d = json.load(f)
            items.append({
                "id": d.get("id"),
                "title": d.get("title") or "គម្រោង",
                "description": (d.get("description") or "")[:160],
                "template": d.get("template"),
                "updated_at": d.get("updated_at"),
                "message_count": len(d.get("messages") or []),
                "file_count": len(d.get("files") or {}),
            })
        except Exception:
            continue
    return items

def _call_grok(messages, max_tokens=8192):
    if not GROK_API_KEY:
        return None, "មិនទាន់កំណត់ GROK_API_KEY នៅលើ server។"
    try:
        r = requests.post(
            GROK_API_URL,
            headers={"Authorization": f"Bearer {GROK_API_KEY}", "Content-Type": "application/json"},
            json={"model": GROK_MODEL, "messages": messages, "temperature": 0.7, "max_tokens": max_tokens},
            timeout=120,
        )
    except requests.RequestException as e:
        return None, f"មិនអាចភ្ជាប់ Grok API៖ {e}"
    if r.status_code != 200:
        try:
            detail = r.json()
        except Exception:
            detail = r.text[:400]
        return None, f"Grok API error ({r.status_code}): {detail}"
    body = r.json()
    try:
        return body["choices"][0]["message"]["content"], None
    except (KeyError, IndexError, TypeError):
        return None, "ចម្លើយពី API មិនត្រឹមត្រូវ"

def _extract_files_from_reply(reply: str):
    files = {}
    pattern = re.compile(r"```(?:([\w./\\-]+)|(?:\w+)\s+([\w./\\-]+))\n(.*?)```", re.S)
    for m in pattern.finditer(reply or ""):
        name = (m.group(1) or m.group(2) or "").strip()
        body = (m.group(3) or "").strip()
        if name in ("python", "js", "javascript", "html", "css", "json", "bash", "text", "xml", "env"):
            continue
        if name and body and len(name) < 180 and ("." in name or "/" in name):
            files[name] = body
    return files


@app.get("/")
def index():
    return send_from_directory(".", "index.html")

@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "service": "Kairozen AI",
        "grok_configured": bool(GROK_API_KEY),
        "model": GROK_MODEL,
        "projects": len(_list_projects()),
    })

@app.get("/api/templates")
def api_templates():
    return jsonify({
        "templates": [
            {"id": k, "title": v["title"], "description": v["description"]}
            for k, v in TEMPLATES.items()
        ]
    })

@app.get("/api/security-guide")
def api_security_guide():
    return jsonify(SECURITY_GUIDE)

@app.get("/api/projects")
def api_list_projects():
    return jsonify({"projects": _list_projects()})

@app.post("/api/projects")
def api_create_project():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip() or "គម្រោងថ្មី"
    description = (data.get("description") or "").strip()
    template = (data.get("template") or "").strip()
    auto_start = bool(data.get("auto_start"))

    if template in TEMPLATES and not description:
        description = TEMPLATES[template]["description"]
    if template in TEMPLATES and title == "គម្រោងថ្មី":
        title = TEMPLATES[template]["title"]

    pid = uuid.uuid4().hex[:12]
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    proj = {
        "id": pid,
        "title": title[:120],
        "description": description[:2000],
        "template": template or None,
        "created_at": now,
        "updated_at": now,
        "messages": [],
        "files": {},
    }
    with _lock:
        _save_project(proj)

    bootstrap = None
    if auto_start and template in TEMPLATES:
        # return starter prompt for client to send, or run one shot
        starter = TEMPLATES[template]["starter"]
        system = SYSTEM_BASE + PROJECT_EXTRA + f"\n\nឈ្មោះគម្រោង: {title}\nពិពណ៌នា: {description}\n"
        system += "\nរបៀប: សរសេរ code ពេញ។ ប្រើ ```path/file.ext"
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": starter},
        ]
        reply, err = _call_grok(messages)
        if not err and reply:
            proj["messages"].append({"role": "user", "content": starter, "ts": now})
            proj["messages"].append({"role": "assistant", "content": reply, "ts": now})
            new_files = _extract_files_from_reply(reply)
            if new_files:
                proj["files"].update(new_files)
            proj["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            with _lock:
                _save_project(proj)
            bootstrap = {"reply": reply, "files_updated": list(new_files.keys())}
        elif err:
            bootstrap = {"error": err}

    return jsonify({"project": proj, "bootstrap": bootstrap})

@app.get("/api/projects/<pid>")
def api_get_project(pid):
    proj = _load_project(pid)
    if not proj:
        return jsonify({"error": "រកមិនឃើញគម្រោង"}), 404
    return jsonify({"project": proj})

@app.delete("/api/projects/<pid>")
def api_delete_project(pid):
    path = _proj_path(pid)
    if path.exists():
        path.unlink()
    return jsonify({"ok": True})

@app.post("/api/projects/<pid>/chat")
def api_project_chat(pid):
    proj = _load_project(pid)
    if not proj:
        return jsonify({"error": "រកមិនឃើញគម្រោង"}), 404
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "សូមវាយសារ។"}), 400
    if len(message) > 8000:
        return jsonify({"error": "សារវែងពេក។"}), 400

    mode = (data.get("mode") or "build").strip()
    mode_hint = {
        "plan": "របៀប៖ រៀបផែនការ / outline ជំហានៗ។",
        "code": "របៀប៖ សរសេរ code ពេញ។ ប្រើ ```path/file.ext",
        "review": "របៀប៖ ពិនិត្យ code/file បច្ចុប្បន្ន — bug, security គោលការណ៍, កែលម្អ។",
        "build": "របៀប៖ បន្តកសាង។ បើមាន file ថ្មី ប្រើ ```path/file.ext",
        "secure": "របៀប៖ ពិនិត្យ security គោលការណ៍ (env, validation, auth) — មិនមែន attack guide។",
    }.get(mode, "")

    files = proj.get("files") or {}
    file_summary = ""
    if files:
        names = list(files.keys())[:40]
        file_summary = "\n\nFile ក្នុងគម្រោង:\n- " + "\n- ".join(names)
        for fn in names[:8]:
            content = files[fn]
            if len(content) < 2500:
                file_summary += f"\n\n### {fn}\n```\n{content[:2000]}\n```"

    system = SYSTEM_BASE + PROJECT_EXTRA
    system += f"\n\nឈ្មោះគម្រោង: {proj.get('title')}"
    if proj.get("description"):
        system += f"\nពិពណ៌នា: {proj.get('description')}"
    if proj.get("template"):
        system += f"\nTemplate: {proj.get('template')}"
    if mode_hint:
        system += "\n" + mode_hint
    system += file_summary

    messages = [{"role": "system", "content": system}]
    for h in (proj.get("messages") or [])[-16:]:
        role, content = h.get("role"), (h.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content[:6000]})
    messages.append({"role": "user", "content": message})

    reply, err = _call_grok(messages)
    if err:
        return jsonify({"error": err}), 502

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    proj.setdefault("messages", []).append({"role": "user", "content": message, "ts": now})
    proj["messages"].append({"role": "assistant", "content": reply, "ts": now})
    if len(proj["messages"]) > 80:
        proj["messages"] = proj["messages"][-80:]

    new_files = _extract_files_from_reply(reply)
    if new_files:
        proj.setdefault("files", {}).update(new_files)
    proj["updated_at"] = now
    with _lock:
        _save_project(proj)

    return jsonify({
        "reply": reply,
        "files_updated": list(new_files.keys()),
        "project": {
            "id": proj["id"],
            "title": proj["title"],
            "file_count": len(proj.get("files") or {}),
            "message_count": len(proj.get("messages") or []),
        },
    })

@app.post("/api/chat")
def api_quick_chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    history = data.get("history") or []
    if not message:
        return jsonify({"error": "សូមវាយសារ។"}), 400
    messages = [{"role": "system", "content": SYSTEM_BASE}]
    for h in history[-10:]:
        role, content = h.get("role"), (h.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content[:4000]})
    messages.append({"role": "user", "content": message})
    reply, err = _call_grok(messages)
    if err:
        return jsonify({"error": err}), 502
    return jsonify({"reply": reply})

@app.get("/api/projects/<pid>/files")
def api_list_files(pid):
    proj = _load_project(pid)
    if not proj:
        return jsonify({"error": "រកមិនឃើញគម្រោង"}), 404
    files = proj.get("files") or {}
    return jsonify({"files": [{"path": k, "size": len(v)} for k, v in sorted(files.items())]})

@app.get("/api/projects/<pid>/files/<path:fpath>")
def api_get_file(pid, fpath):
    proj = _load_project(pid)
    if not proj:
        return jsonify({"error": "រកមិនឃើញគម្រោង"}), 404
    content = (proj.get("files") or {}).get(fpath)
    if content is None:
        return jsonify({"error": "រកមិនឃើញ file"}), 404
    return jsonify({"path": fpath, "content": content})

if __name__ == "__main__":
    _ensure_dirs()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
