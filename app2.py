from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Inicializa o servidor Flask
app = Flask(__name__)

# Rota principal para receber as informações e fazer o scraping
@app.route('/buscar_orcamento', methods=['POST'])
def buscar_orcamento():
    # Recebe os dados da requisição POST
    data = request.json
    data_checkin = data['checkin']
    data_checkout = data['checkout']
    numero_adultos = data['adults']

    # Chama a função que usa Selenium para buscar o orçamento
    orcamentos = buscar_orcamento_selenium(data_checkin, data_checkout, numero_adultos)

    # Retorna o resultado em formato JSON
    return jsonify({"orcamentos": orcamentos})

# Função que usa Selenium para buscar os orçamentos
def buscar_orcamento_selenium(data_checkin, data_checkout, numero_adultos):
    # Caminho para o ChromeDriver
    PATH = "caminho/para/o/chromedriver"  # Substitua pelo caminho correto do seu ChromeDriver

    # Inicia o navegador controlado pelo Selenium
    driver = webdriver.Chrome(PATH)

    # Abre o site de reservas
    driver.get("https://admin.hqbeds.com.br/hq/admin/integrations/home")

    time.sleep(2)  # Espera a página carregar

    # Preenche os campos de check-in, check-out e número de adultos (ajuste conforme o site real)
    checkin_input = driver.find_element(By.ID, "checkin")  # Ajustar ID do campo
    checkin_input.clear()
    checkin_input.send_keys(data_checkin)

    checkout_input = driver.find_element(By.ID, "checkout")  # Ajustar ID do campo
    checkout_input.clear()
    checkout_input.send_keys(data_checkout)

    adultos_input = driver.find_element(By.ID, "adults")  # Ajustar ID do campo
    adultos_input.clear()
    adultos_input.send_keys(numero_adultos)

    # Clica no botão de buscar (ajustar conforme o site real)
    buscar_button = driver.find_element(By.ID, "buscar")  # Ajustar ID do botão
    buscar_button.click()

    time.sleep(5)  # Espera os resultados carregarem

    # Captura os preços e opções de orçamento
    resultados = driver.find_elements(By.CLASS_NAME, "price")  # Ajustar classe conforme o site
    orcamentos = [resultado.text for resultado in resultados]

    # Fecha o navegador
    driver.quit()

    return orcamentos

# Inicia o servidor Flask
if __name__ == '__main__':
    app.run(debug=True)

