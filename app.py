from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time
import os

app = Flask(__name__)

# Função para buscar orçamentos usando Selenium
def buscar_orcamento(data_checkin, data_checkout, numero_adultos, numero_menores=0):
    orcamentos = []

    # Caminho correto para o executável do ChromeDriver
    PATH = "C:/webdriver/chromedriver-win64/chromedriver.exe"
    service = Service(PATH)

    # Configurar o Chrome para rodar em modo headless
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Executar sem interface gráfica
    options.add_argument('--no-sandbox')  # Segurança extra para servidores
    options.add_argument('--disable-dev-shm-usage')  # Melhor desempenho em containers

    driver = webdriver.Chrome(service=service, options=options)

    try:
        print("Montando a URL de pesquisa...")
        # Construir a URL baseada nos parâmetros fornecidos
        url = f"https://booking.hqbeds.com.br/bichopreguica/rooms?arrival={data_checkin}&departure={data_checkout}&coupon=&adults={numero_adultos}&children={numero_menores}"

        print(f"Navegando para: {url}")
        # Navegar para a URL diretamente
        driver.get(url)

        # Aumentar o tempo de espera para garantir que os resultados sejam carregados
        print("Aguardando o carregamento da página...")
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CLASS_NAME, "currency"))
        )

        # Esperar mais tempo para garantir que todos os elementos tenham sido carregados
        print("Esperando mais 10 segundos para garantir o carregamento completo...")
        time.sleep(10)

        print("Resultados carregados. Coletando informações...")

        # Capturar todos os blocos que contêm as informações de pessoas, preços e disponibilidade
        blocos_quartos = driver.find_elements(By.CSS_SELECTOR, "div.d-flex.align-items-center.flex-row.justify-content-end")

        for bloco in blocos_quartos:
            try:
                disponivel = bloco.find_elements(By.CSS_SELECTOR, "button.btn.btn-raised.btn-orange.slim.text-uppercase")
                pessoas = bloco.find_element(By.CSS_SELECTOR, "label.text-secondary").text.strip()

                if not disponivel:
                    print(f"Quarto para {pessoas} pessoas não está disponível, pulando...")
                    continue

                preco = bloco.find_element(By.CSS_SELECTOR, "span.value.currency").text.strip()
                orcamentos.append((pessoas, preco))
            except Exception as e:
                print(f"Erro ao processar o bloco de quartos: {e}")
                continue

    except TimeoutException:
        print("O tempo de carregamento foi excedido.")
    finally:
        driver.quit()

    return orcamentos

# Rota para buscar orçamentos
@app.route('/buscar_orcamento', methods=['POST'])
def buscar():
    data = request.json
    data_checkin = data.get('data_checkin')
    data_checkout = data.get('data_checkout')
    numero_adultos = data.get('numero_adultos')
    numero_menores = data.get('numero_menores', 0)  # Valor padrão de 0 se não for fornecido

    if not data_checkin or not data_checkout or not numero_adultos:
        return jsonify({'error': 'Faltam parâmetros obrigatórios'}), 400

    # Executar a função buscar_orcamento
    orcamentos = buscar_orcamento(data_checkin, data_checkout, numero_adultos, numero_menores)
    
    return jsonify({'orcamentos': orcamentos})

# Iniciar o servidor Flask no ambiente de produção
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))  # Usar a variável de ambiente PORT fornecida pela Railway
    app.run(host="0.0.0.0", port=port)  # Ouvir em todas as interfaces de rede (0.0.0.0)
