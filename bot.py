from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import telegram
import asyncio
import schedule
import time
from datetime import datetime, timedelta


# Replace with your Telegram bot token
TELEGRAM_BOT_TOKEN = '7169231414:AAFF1PBSQ-dJxATs-p2MAWXpKluFmNJRGrw'
# Replace with your Telegram chat ID
TELEGRAM_CHAT_ID = '5184653808'

INITIAL_URL = 'https://www.exteriores.gob.es/Consulados/lahabana/es/ServiciosConsulares/Paginas/index.aspx?scca=Familia&scco=Cuba&scd=166&scs=Nacimientos'

async def send_telegram_message(message):
    bot = telegram.Bot(TELEGRAM_BOT_TOKEN)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

def wait_for_loader(driver, timeout=10):
    def loader_not_visible(d):
        try:
            loader = d.find_element(By.CLASS_NAME, "clsBktWidgetDefaultLoading")
            return not loader.is_displayed()
        except NoSuchElementException:
            return True

    WebDriverWait(driver, timeout).until(loader_not_visible)

def unlock():
    options = webdriver.ChromeOptions()
##    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)

    try:
        # Navigate to the initial page
        driver.get(INITIAL_URL)
        wait_for_loader(driver)

        # Click on "Solicitar certificación de Nacimiento para DNI"
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Reservar cita de Inscripción directa de menores"))
        ).click()

        # Switch to the new window
        driver.switch_to.window(driver.window_handles[-1])

        # Accept the alert if it appears
        try:
            WebDriverWait(driver, 45).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
        except TimeoutException:
            print("Intento Fallido al desbloquear la web")
            driver.quit()
            return False
        # Click on "Continuar" button
        WebDriverWait(driver, 45).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continuar')]"))
        ).click()

        try:
            WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "clsBktWidgetDefaultLoading")))
            return check_appointments(driver)
        except:
            print("La clase clsBktWidgetDefaultLoading no se encuentra")
            driver.quit()
            return False
        
    except Exception as e:
        print(f"Error al verificar citas: {e}")
        driver.quit()
        return False

    
def check_appointments(driver):  
        # Check for available appointments
        try: 
            try:
                # Esperar a que aparezca uno de los dos elementos: una cita disponible o el texto "No hay citas"
                WebDriverWait(driver, 100).until(
                    lambda d: (
                        d.find_elements(By.CLASS_NAME, "clsDivDatetimeSlot") or
                        d.find_elements(By.ID, "idDivNotAvailableSlotsTextTop")
                    )
                )

                # Comprobar si hay citas disponibles
                if driver.find_elements(By.CLASS_NAME, "clsDivDatetimeSlot"):
                    print("¡Citas disponibles!")
                    asyncio.run(send_telegram_message("¡Hay citas disponibles para DNI !"))
                    driver.quit()
                    return True
                elif driver.find_elements(By.ID, "idDivNotAvailableSlotsTextTop"):
                    print("No hay citas disponibles en este momento.")
                    driver.quit()
                    return True
                else:
                    print("No se pudo determinar el estado de las citas.")
                    driver.quit()
                    return False
            except TimeoutException:
                print("Tiempo de espera agotado. No se encontró ningún elemento relevante.")
                driver.quit()
                return False
        except:
            print("Algo salio mal") 
            driver.quit()      
            return False    
    

def run_at_specific_time():
    now = datetime.now()
    if now.minute == 10:
        check_appointments()

def main():
    print("Bot iniciado.")
    estado=False
    while not estado:
        estado = unlock()

if __name__ == "__main__":
    main()
