from quart import  render_template
from htnats import headlineget


def init(app):
    app.add_url_rule('/stand2', view_func=stand2)


#@app.route("/stand2")
async def stand2():
    headline =  headlineget()
    headings = []
    for i in headline:
        headings.append(i[0])
    return await render_template('stand2.html',headings=headings)

