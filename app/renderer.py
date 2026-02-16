import html

def escape(s):
    return html.escape(str(s) if s else "")

class Renderer:
    @staticmethod
    def render_threads(threads, lang):
        lines = []
        for th in threads:
            url = f"/{lang}/t/{th['thread_id']}"
            last = th['last_at'].strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f'''
    <a class="thread" href="{url}">
      <div class="thread-top">
        <div class="thread-title">#{th['thread_id']} {escape(th['preview'])}</div>
        <div class="thread-meta">replies: {th['replies']} / last: {last} UTC</div>
      </div>
      <div class="muted">by {escape(th['name'])}</div>
    </a>''')
        return "\n".join(lines)

    @staticmethod
    def render_tree(tree, lang):
        lines = []
        for node in tree:
            lines.append(Renderer._render_node(node, 0, lang))
        return "\n".join(lines)

    @staticmethod
    def _render_node(node, depth, lang):
        p = node["post"]
        is_ai = p.is_ai
        cls = "ai" if is_ai else "human"
        name_cls = "ai-name" if is_ai else "human-name"
        prefix = "AI-" if is_ai else ""
        name = f"{prefix}{escape(p.name)}"
        
        reply_anchor = f'<span class="muted">(>>{p.reply_to_id})</span>' if p.reply_to_id else ""
        
        # Reply form (simplified)
        reply_text = "このレスに返信" if lang=="jp" else "Reply"
        placeholder = "返信..." if lang=="jp" else "Reply..."
        
        # Options
        opts_jp = '''
          <option value="風吹けば名無し">風吹けば名無し (Meme/Short)</option>
          <option value="冷静マン">冷静マン (Logical)</option>
          <option value="ツッコミ隊">ツッコミ隊 (Skeptic)</option>
          <option value="経験者ニキ">経験者ニキ (Experienced)</option>'''
        opts_en = '''
          <option value="Anon">Anon (Meme/Short)</option>
          <option value="Skeptic">Skeptic (Critical)</option>
          <option value="Pragmatist">Pragmatist (Logical)</option>
          <option value="BeenThere">BeenThere (Experienced)</option>'''
        opts = opts_jp if lang=="jp" else opts_en
        
        check_text_multi = "AIが複数人でレス（2ch風）" if lang=="jp" else "AI multi-replies (forum vibe)"
        check_text_single = "AI単発返信（1件）" if lang=="jp" else "Single AI reply"
        
        html_chunk = f'''
  <article class="post {cls}" style="--depth: {depth}; margin-left: calc(var(--depth) * 18px);">
    <div class="post-head">
      <div class="name">
        <span class="name {name_cls}">{name}</span>
        {reply_anchor}
        <span class="muted"> #{p.id}</span>
      </div>
      <div class="time">{p.created_at.strftime("%Y-%m-%d %H:%M:%S")} UTC</div>
    </div>
    <div class="content">{escape(p.content)}</div>

    <details class="replybox">
      <summary class="replybtn">{reply_text}</summary>
      <form class="form" method="post" action="/new">
        <input type="hidden" name="lang" value="{lang}" />
        <input type="hidden" name="reply_to_id" value="{p.id}" />

        <label class="label">Name</label>
        <input class="input" name="name" placeholder="Anonymous" maxlength="50" />

        <label class="label">Reply</label>
        <textarea class="textarea" name="content" placeholder="{placeholder}" maxlength="2000" required></textarea>

        <label class="label">AI Persona (Optional)</label>
        <select class="input" name="ai_persona">
          <option value="">-- Random / Default --</option>
          {opts}
        </select>

        <label class="check">
          <input type="checkbox" name="ai_multi" value="1" />
          <span>{check_text_multi}</span>
        </label>

        <label class="check">
          <input type="checkbox" name="ai" value="1" />
          <span>{check_text_single}</span>
        </label>

        <button class="btn" type="submit">Send</button>
      </form>
    </details>
  </article>'''
        
        # Recursion
        children_html = []
        for child in node["children"]:
            children_html.append(Renderer._render_node(child, depth + 1, lang))
            
        return html_chunk + "".join(children_html)

    @staticmethod
    def render_layout(title, body, lang):
        # Inline base.html logic
        header_title = title or "BBS"
        
        return f'''<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{escape(header_title)}</title>
  <link rel="stylesheet" href="/static/style.css"/>
  <script defer src="/static/app.js"></script>
</head>
<body>
  <div class="container">
    <header class="header">
      <div class="brand">
        <div class="logo">B</div>
        <div>
          <h1 class="h1">{escape(header_title)}</h1>
          <div class="sub">local dev</div>
        </div>
      </div>
    </header>

    <main>
      {body}
    </main>

    <footer class="footer">© evolvion-bbs</footer>
  </div>
</body>
</html>'''

    @staticmethod
    def render_index(title, lang, threads_html):
        h2_title = "日本語板" if lang == "jp" else "English Board"
        h2_new = "新規スレッド作成" if lang == "jp" else "Create a new thread"
        ph_content = "スレ本文..." if lang == "jp" else "Thread text..."
        btn_create = "Create Thread"
        h2_list = "スレ一覧" if lang == "jp" else "Threads"
        
        opts_jp = '''<option value="風吹けば名無し">風吹けば名無し (Meme/Short)</option> ...''' # truncated for brevity in code, but full in implementation
        # Actually I can just reuse the generic structure.
        
        # Simplified options for index
        # To avoid duplicating logic, I'll put direct HTML here.
        
        body = f'''
<section class="card">
  <div class="row">
    <h2 class="h2">{h2_title}</h2>
    <div class="muted">
      <a href="/jp">/jp</a> | <a href="/en">/en</a>
    </div>
  </div>
</section>

<section class="card">
  <h2 class="h2">{h2_new}</h2>
  <form class="form" method="post" action="/new">
    <input type="hidden" name="lang" value="{lang}" />
    <label class="label">Name</label>
    <input class="input" name="name" placeholder="Anonymous" maxlength="50" />
    <label class="label">Content</label>
    <textarea class="textarea" name="content" placeholder="{ph_content}" maxlength="2000" required></textarea>
    <label class="label">AI Persona</label>
    <select class="input" name="ai_persona"><option value="">-- Defaults --</option></select>
    <div class="check"><input type="checkbox" name="ai_multi" value="1"> <span>Multi AI</span></div>
    <div class="check"><input type="checkbox" name="ai" value="1"> <span>Single AI</span></div>
    <button class="btn" type="submit">{btn_create}</button>
  </form>
</section>

<section class="card">
  <h2 class="h2">{h2_list}</h2>
  <div class="threads">
    {threads_html}
  </div>
</section>'''
        return Renderer.render_layout(title, body, lang)

    @staticmethod
    def render_thread_page(title, lang, thread_id, tree_html, is_locked):
        h2_title = "スレッド" if lang=="jp" else "Thread"
        back_text = "スレ一覧へ" if lang=="jp" else "Back to threads"
        reply_header = "返信する" if lang=="jp" else "Reply"
        
        lock_msg = ""
        if is_locked:
            msg = "このスレッドはロックされています。" if lang=="jp" else "This thread is locked."
            lock_msg = f'<div class="muted">{msg}</div>'
            form_html = ""
        else:
            # Main reply form at top
            ph_reply = "返信..." if lang=="jp" else "Reply..."
            btn_send = "Send Reply"
            form_html = f'''
  <form class="form" method="post" action="/new">
    <input type="hidden" name="lang" value="{lang}" />
    <input type="hidden" name="reply_to_id" value="{thread_id}" />
    <label class="label">Name</label>
    <input class="input" name="name" placeholder="Anonymous" maxlength="50" />
    <label class="label">Reply</label>
    <textarea class="textarea" name="content" placeholder="{ph_reply}" maxlength="2000" required></textarea>
    <button class="btn" type="submit">{btn_send}</button>
  </form>'''

        body = f'''
<section class="card">
  <div class="row">
    <h2 class="h2">{h2_title} #{thread_id}</h2>
    <div class="muted">
      <a href="/{lang}">← {back_text}</a>
    </div>
  </div>
</section>

<section class="card">
  <h2 class="h2">{reply_header}</h2>
  {lock_msg}
  {form_html}
</section>

<section class="card">
  <div class="tree">
    {tree_html}
  </div>
</section>'''
        return Renderer.render_layout(title, body, lang)
