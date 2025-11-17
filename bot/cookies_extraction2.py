import browser_cookie3

cj = browser_cookie3.chrome(domain_name='logement.cesal.fr')
cookie_string = "\n".join([f"{c.name};{c.value};{c.domain}" for c in cj])
print(cookie_string)
