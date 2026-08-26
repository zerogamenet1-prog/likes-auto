from pathlib import Path

p = Path(r"C:\Users\VIPLIKE\Desktop\likes-auto.com\py-app\templates\admin\settings_hub.html")
text = p.read_text(encoding="utf-8")

# general: keep shop chips, drop customer menu chips
old_menu = text[text.find('      <p class="adm-sw-k">\u0e40\u0e21\u0e19\u0e39\u0e25\u0e39\u0e01\u0e04\u0e49\u0e32</p>'):]
end_menu = old_menu.find("    <div class=\"adm-form-grid\"")
if end_menu < 0:
    raise SystemExit("menu chips end missing")
text = text[:text.find('      <p class="adm-sw-k">\u0e40\u0e21\u0e19\u0e39\u0e25\u0e39\u0e01\u0e04\u0e49\u0e32</p>')] + old_menu[end_menu:]

text = text.replace(
    '<details class="adm-more" id="menu-mods"{% if saved %} open{% endif %}>',
    '<details class="adm-more"{% if saved %} open{% endif %}>',
    1,
)
text = text.replace(
    '<script>if(location.hash===\'#menu-mods\'){var d=document.getElementById(\'menu-mods\'); if(d) d.open=true;}</script>\n',
    '',
    1,
)

def sw(name, label):
    return (
        '        <label class="adm-sw"><input type="checkbox" name="%s" value="1" '
        "{%% if settings.get('%s', '1') != '0' %%}checked{%% endif %%}> %s</label>\n"
        % (name, name, label)
    )

mods = """{% if tab=='modules' %}
<form method="post" class="adm-form adm-form-wide">
  <p class="adm-help">\u0e15\u0e34\u0e4a\u0e01\u0e40\u0e1e\u0e37\u0e48\u0e2d\u0e40\u0e1b\u0e34\u0e14\u0e40\u0e21\u0e19\u0e39\u0e43\u0e2b\u0e49\u0e25\u0e39\u0e01\u0e04\u0e49\u0e32\u0e40\u0e2b\u0e47\u0e19 \u0e16\u0e49\u0e32\u0e1b\u0e34\u0e14\u0e41\u0e25\u0e49\u0e27\u0e40\u0e02\u0e49\u0e32\u0e2b\u0e19\u0e49\u0e32\u0e19\u0e31\u0e49\u0e19\u0e44\u0e21\u0e48\u0e44\u0e14\u0e49</p>
  <div class="adm-sw-box">
    <p class="adm-sw-k">\u0e04\u0e33\u0e2a\u0e31\u0e48\u0e07\u0e0b\u0e37\u0e49\u0e2d</p>
    <div class="adm-sw-row">
""" + sw("mod_neworder", "\u0e2a\u0e31\u0e48\u0e07\u0e0b\u0e37\u0e49\u0e2d\u0e43\u0e2b\u0e21\u0e48") + sw("mod_dripfeed", "\u0e2a\u0e48\u0e07\u0e17\u0e35\u0e25\u0e30\u0e23\u0e2d\u0e1a") + sw("mod_services", "\u0e1a\u0e23\u0e34\u0e01\u0e32\u0e23") + sw("mod_orders", "\u0e1b\u0e23\u0e30\u0e27\u0e31\u0e15\u0e34") + sw("mod_subscription", "\u0e40\u0e15\u0e34\u0e21\u0e2d\u0e31\u0e15\u0e42\u0e19\u0e21\u0e31\u0e15\u0e34") + """    </div>
    <p class="adm-sw-k">\u0e40\u0e07\u0e34\u0e19</p>
    <div class="adm-sw-row">
""" + sw("mod_addfunds", "\u0e40\u0e15\u0e34\u0e21\u0e40\u0e07\u0e34\u0e19") + sw("mod_affiliate", "\u0e40\u0e0a\u0e34\u0e0d\u0e40\u0e1e\u0e37\u0e48\u0e2d\u0e19") + sw("mod_child", "\u0e41\u0e1c\u0e07\u0e25\u0e39\u0e01") + sw("mod_transfer", "\u0e42\u0e2d\u0e19\u0e40\u0e07\u0e34\u0e19") + """    </div>
    <p class="adm-sw-k">\u0e0a\u0e48\u0e27\u0e22\u0e40\u0e2b\u0e25\u0e37\u0e2d</p>
    <div class="adm-sw-row">
""" + sw("mod_tickets", "\u0e0b\u0e31\u0e1e\u0e1e\u0e2d\u0e23\u0e4c\u0e15") + sw("mod_faq", "FAQ") + """    </div>
    <p class="adm-sw-k">\u0e2d\u0e37\u0e48\u0e19\u0e46</p>
    <div class="adm-sw-row">
""" + sw("mod_account", "\u0e1a\u0e31\u0e0d\u0e0a\u0e35") + sw("mod_api", "API") + sw("mod_logout", "\u0e2d\u0e2d\u0e01") + """    </div>
  </div>
  <button class="la-btn" type="submit">\u0e1a\u0e31\u0e19\u0e17\u0e36\u0e01</button>
</form>
{% endif %}
"""

start = text.find("{% if tab=='modules' %}")
end = text.find("{% if tab=='integrations' %}")
if start < 0 or end < 0:
    raise SystemExit("modules block markers missing")
text = text[:start] + mods + "\n" + text[end:]
p.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
print("ok", text.count("mod_neworder"), "general menu", "mod_neworder" in text[text.find("tab=='general'"):text.find("tab=='currency'")])
