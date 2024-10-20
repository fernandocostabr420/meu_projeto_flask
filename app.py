from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time

app = Flask(__name__)

# Função para converter o preço para um valor numérico (float)
def converter_preco(preco_str):
    return float(preco_str.replace("R$", "").replace(".", "").replace(",", "."))

# Função para buscar orçamentos usando Selenium
def buscar_orcamento(data_checkin, data_checkout, numero_adultos, numero_menores=0):
    orcamentos = []
    total_pessoas = numero_adultos + numero_menores  # Total de pessoas solicitadas

    # Caminho correto para o executável do ChromeDriver
    PATH = "/usr/local/bin/chromedriver"  # Ajustar para o ambiente de produção
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

                # Verificar se o número de pessoas do quarto corresponde ao número solicitado
                if int(pessoas) != total_pessoas:
                    print(f"Quarto para {pessoas} pessoas não corresponde ao solicitado ({total_pessoas} pessoas), pulando...")
                    continue

                if not disponivel:
                    print(f"Quarto para {pessoas} pessoas não está disponível, pulando...")
                    continue

                preco = bloco.find_element(By.CSS_SELECTOR, "span.value.currency").text.strip()

                # Adicionar "pessoas" ao lado do número de pessoas
                orcamentos.append((pessoas + " pessoas", preco))
            except Exception as e:
                print(f"Erro ao processar o bloco de quartos: {e}")
                continue

    except TimeoutException:
        print("O tempo de carregamento foi excedido.")
    finally:
        driver.quit()

    # Ordenar os orçamentos pelo preço (conversão de string para valor numérico)
    if orcamentos:
        orcamentos.sort(key=lambda x: converter_preco(x[1]))
        # Retornar apenas o orçamento mais barato
        return [orcamentos[0]]  # Pegando apenas o orçamento mais barato
    else:
        print("Nenhum resultado encontrado.")
        return []

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

