
from jinja2 import Template

netsoc = Template("""
<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width">
        <style>
                @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@100;300;400;500;700;900&display=swap');

                html, body {
                        margin: 0;
                        padding: 0;
                        font-size: 14px;
                        font-weight: 400;
                        font-family: 'Roboto', sans-serif !important;
                        color: white;
                        overflow-x: hidden;
                }
        </style>
    </head>
    <body style="margin: 0 auto;padding: 0;font-size: 14px;font-weight: 400 !important;color: white;overflow-x: hidden;font-family: 'Roboto', sans-serif !important;">
        <div id="body" style="margin: 0 auto;background-color: rgb(33,33,33);height: 100%;position: absolute;width: 100%;">
            <div id="kc-header" class="" style="height: 64px;background-color: #2196F3;position: relative;z-index: 2;box-shadow: 0px 0px 8px rgba(0,0,0,0.35);margin: 0 auto;">
                <div id="kc-header-wrapper" class="" style="position: relative;height: 64px;display: block;text-align: center;">
                        <img src="https://raw.githubusercontent.com/UCCNetsoc/wiki/master/assets/logo-horizontal-inverted.png" style="height: 32px;margin: 16px auto;padding: 0;">
                </div>
            </div>
            <h1 style="color: white; font-size: 18px;font-weight: 200;text-align: center;padding: 8px 0;">
                {{ heading }}
            </h1>
            <div style="max-width: 600px; margin: 1em auto">
                <p style="border-top: 1px solid rgb(55,55,55);border-bottom: 1px solid rgb(55,55,55);color: white;text-align: center;max-width: 500px;color: #fff;padding: 1em;">
                    {{ paragraph }}
                </p>
            </div>
            <div style="max-width: 1000px; margin: 1em auto">
                {% if embeds is defined %}
                    {% for item in embeds %}
                        <div style="background-color: #111;max-width: fit-content; width:min-content; margin: 10px auto 10px auto;padding: 10px; border-left: #2196F3 solid 4px;">
                            {{ item.text }}
                        </div>
                    {% endfor %}
                {% endif %}

                {% if buttons is defined %}
                    {% for item in buttons %}
                        <a class="btn" clicktracking=off href="{{ item.link }}" style="color: white;display: block;width: 100%;text-align: center;margin: 2em auto;text-transform: uppercase;border-radius: 4px;font-size: 14px;background-color: #2196F3;letter-spacing: 0.09em;border: none;font-weight: 500;padding: 16px 0;line-height: 0px;cursor: pointer;max-width: 200px;text-decoration: none;font-family: 'Roboto', sans-serif !important;">
                            {{ item.text }}
                        </a>
                    {% endfor %}
                {% endif %}
            </div>
            <footer style="color: white;font-size: .8em;text-align: center;max-width: 500px;margin: 1em auto 3em auto;padding-bottom:3em;">
                <a target="_blank" clicktracking="off" style="color: white;" href="https://discord.netsoc.co">Discord</a>
                <span> &bull; </span>
                <a target="_blank" clicktracking="off" style="color: white;" href="https://wiki.netsoc.co/en/services/terms-of-service">Terms of Service</a>
            </footer>
        </div>
    </body>
</html>
""")

