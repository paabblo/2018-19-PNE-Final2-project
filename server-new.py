from http.server import BaseHTTPRequestHandler
import socketserver
import requests
import termcolor

def error_page():
    file = open("Error.html", "r")
    return file.read()
# ----------------------------------------------

class MyServer(BaseHTTPRequestHandler):
    URL = 'https://rest.ensembl.org'

    def get_parameter(self):
        if self.path.find('?') > 0:
            input = self.path.split('?')[1]
            if len(input) == 0:
                return False
            if input.find('='):
                if input.find('&') > 0:
                    first_input = input.split("&")[0]
                    second_input = input.split("&")[1]
                    first_parameter = first_input.split("=")[1]
                    second_parameter = second_input.split("=")[1]
                    if first_input.split("=")[0] == "specie":
                        return first_parameter, second_parameter
                    elif first_input.split("=")[0] == "chromo":
                        return second_parameter, first_parameter
                    else:
                        return False
                else:
                    input_value = input.split("=")[1]
                    return input_value
            else:
                return False
        else:
            return False

    def do_GET(self):
        global html_content
        termcolor.cprint("client request: " + self.path, 'green')
        function = self.path.split("?")[0]
    # SHOW INDEX PAGE
        if function == "/":
            html_file = open("index.html", "r")
            html_content = html_file.read()
    # SHOW BASIC PAGE
        elif function == "/listSpecies":
            parameter = self.get_parameter()
            try:
                # 'isinstance(object, str)' will return True if 'object' is 'string'
                if isinstance(parameter, str):
                    species_list = self.list_species(int(parameter))
                else:
                    species_list = self.list_species("all")
                html_file = open("listSpecies.html", "r")
                html_content = html_file.read()
                html_content += "<hr><h3>Result:</h3><ul>"
                for item in species_list:
                    html_content += "<li>" + item + "</li>"
                html_content += "</ul><div></body></html>"
            except ValueError:
                html_content = error_page()
    # ----------------------------------------------
        elif function == "/karyotype":
            html_file = open("karyotype.html", "r")
            html_content = html_file.read()
            parameter = self.get_parameter()
            if isinstance(parameter, str):
                result = self.karyotype(parameter)
                html_content += "<hr><h3>Result:</h3>"
                if not isinstance(result, list):
                    print(result)
                    html_content += "<p><strong>"+str(result)+"</strong></p>"
                elif len(result) == 0:
                    html_content += "<p><strong>"+parameter.upper()+" has None Karyotype</strong></p>"
                else:
                    html_content += "Karyotype of " + parameter.upper() + ":<ul>"
                    for item in result:
                        html_content += "<li>" + item + "</li>"
            html_content += "<div></body></html>"
    # ----------------------------------------------
        elif function == "/chromosomeLength":
            html_file = open("chromosomeLength.html", "r")
            html_content = html_file.read()
            parameter = self.get_parameter()
            if parameter:
                specie, chromo = parameter
                html_content += "<hr><h3>Result:</h3>"
                html_content += "The Chromosome " + chromo.upper() + " lenght of " + specie.upper() + ": "
                result = self.chromosome_length(specie, chromo.upper())
                html_content += "<strong>" + str(result) + "</strong><div>"

    # ----------------------------------------------
        else:
            html_content = error_page()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', len(str.encode(html_content)))
        self.end_headers()
        self.wfile.write(str.encode(html_content))

# ----------------------------------------------
    def list_species(self, limit):
        endpoint = "/info/species?"
        r = requests.get(self.URL + endpoint, headers={"Content-Type": "application/json"})
        if not r.ok:
            r.raise_for_status()
        decoded = r.json()
        result = decoded.get('species')
        species_list = []
        if limit == 'all':
            n = len(result)
        else:
            n = int(limit)
        counter = 1
        if result:
            for specie in result:
                name = specie['name']
                species_list.append(name)
                if counter < n:
                    counter += 1
                else:
                    break
        return species_list

# ----------------------------------------------
    def karyotype(self, specie):
        endpoint = "/info/assembly/" + specie
        r = requests.get(self.URL + endpoint, headers={"Content-Type": "application/json"})
        if not r.ok:
            try:
                r.raise_for_status()
            except Exception as e:
                return e.args
        decoded = r.json()
        result = decoded['karyotype']
        return result

# ----------------------------------------------
    def chromosome_length(self, specie, chromo):
        endpoint = "/info/assembly/"+specie
        r = requests.get(self.URL + endpoint, headers={"Content-Type": "application/json"})
        if not r.ok:
            try:
                r.raise_for_status()
            except Exception as e:
                return e.args
        decoded = r.json()
        result = decoded.get('top_level_region')
        if result:
            for item in result:
                if item['name'] == chromo:
                    return item['length']
        else:
            return "No results found!"


# ----------------------------------------------
if __name__ == '__main__':
    PORT = 8080
    Handler = MyServer
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("Listening at PORT", PORT)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Server stopped by user")
            httpd.server_close()
