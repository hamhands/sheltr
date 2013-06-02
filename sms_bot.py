import json
import urllib

import tropo
import web

def geocode(location):

    query = urllib.urlencode({'sensor': 'false', 'address': location})
    url = 'http://maps.googleapis.com/maps/api/geocode/json?%s' % query
    resp = urllib.urlopen(url)
    obj = json.load(resp)
    lat = obj['results'][0]['geometry']['location']['lat']
    lon = obj['results'][0]['geometry']['location']['lng']

    return (lat, lon)

class index(object):

    def HEAD(self):

        return

    def POST(self):
        t = tropo.Tropo()
        t.ask(say="", choices="[ANY]")
        t.on(event='continue', next='/getlocation')

        return t.RenderJson()

class getlocation(object):

    def HEAD(self):

        return

    def POST(self):

        print "In getlocation"

        t = tropo.Tropo()
        body = web.ctx.env['wsgi.input'].read()
        print body
        result = tropo.Result(body)
        text = result.getValue().lower()

        option_names = {'food': "food",
                        'shelter': "shelter",
                        'health': "health services"}
        if text in ["food", "shelter", "health"]:
            option = text
            ask_txt = "Searching for %s. What is your location?" %\
                      option_names[option]
            t.ask(say=ask_txt, choices="[ANY]", timeout=30)
            t.on(event="continue", next="/search/%s" % option)
        else:
            t.say("Welcome to sheltr. For food, reply with FOOD. " +\
                  "For shelter, reply with SHELTER. For health services, " +\
                  "reply with HEALTH.")

        return t.RenderJson()

class search(object):

    def POST(self, option):

        t = tropo.Tropo()
        body = web.ctx.env['wsgi.input'].read()
        print body
        result = tropo.Result(body)
        location = result.getValue()

        (lat, lon) = geocode(location)

        print lat, lon

        return search_results.prompt_results(lat, lon, 1)

class search_results(object):

    @classmethod
    def get_results(cls, lat, lon, page):

        real_page = page - 1
        results = [{"name": "Helping Hand Rescue Mission", "dist": 0.2},
                   {"name": "Voyage House", "dist": 0.3},
                   {"name": "My Brothers House", "dist": 0.4},
                   {"name": "Shelter 4", "dist": 0.5},
                   {"name": "Shelter 5", "dist": 0.6},
                   {"name": "Shelter 6", "dist": 0.7}]
        result_slice = results[real_page*3:real_page*3+3]

        print result_slice

        return result_slice

    @classmethod
    def prompt_results(cls, lat, lon, page):

        t = tropo.Tropo()
        real_page = page - 1
        results = search_results.get_results(lat, lon, page)
        result_strs = ["%d. %s (%.1fmi)" % (num+1, r['name'], r['dist'])
                       for num, r in enumerate(results)]
        result_str = "Results: %s 4. More" % " ".join(result_strs)
        t.ask(say=result_str, choices="1,2,3,4", timeout=30, attempts=2)
        next = "/results/%f/%f/%d" % (lat, lon, page)
        t.on(event="continue", next=next)

        return t.RenderJson()

    def get_detail(self, obj):

        t = tropo.Tropo()
        t.say("Info for: %s" % obj['name'])

        return t.RenderJson()

    def POST(self, lat, lon, page):

        lat = float(lat)
        lon = float(lon)
        page = int(page)
        body = web.ctx.env['wsgi.input'].read()
        print body
        result = tropo.Result(body)
        choice = int(result.getValue())
        if choice < 4:
            nearby = search_results.get_results(lat, lon, page)
            print nearby
            response = self.get_detail(nearby[choice-1])
        else:
            response = self.prompt_results(lat, lon, page+1)

        return response

f_re = '([-]?[0-9]+\.?[0-9]+)'

urls = ('/index.json', index,
        '/getlocation', getlocation,
        '/search/([a-z]+)', search,
        '/results/%s/%s/([0-9]+)' % (f_re, f_re), search_results)

application = web.application(urls, globals())

if __name__ == '__main__':
    application.run()
