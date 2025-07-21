import asyncio
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent
from models import JobPosting, JobPortal, SearchFilters, WorkMode, JobType

logger = logging.getLogger(__name__)


class ScraperService:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.daily_limits = {
            JobPortal.LINKEDIN: 20,
            JobPortal.LABORUM: 15, 
            JobPortal.BNE: 25,
            JobPortal.TRABAJANDO: 15
        }
        self.current_counts = {portal: 0 for portal in JobPortal}
        self.last_reset = datetime.utcnow().date()
    
    def _reset_daily_limits(self):
        """Resetear contadores diarios si es un nuevo día"""
        today = datetime.utcnow().date()
        if today > self.last_reset:
            self.current_counts = {portal: 0 for portal in JobPortal}
            self.last_reset = today
            logger.info("Límites diarios reseteados")
    
    def _get_chrome_driver(self) -> webdriver.Chrome:
        """Crear driver de Chrome con configuración anti-detección"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'--user-agent={self.ua.random}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    async def _human_delay(self, min_seconds: float = 2.0, max_seconds: float = 8.0):
        """Simular delays humanos"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def search_jobs(self, filters: SearchFilters) -> List[JobPosting]:
        """Buscar trabajos en todos los portales configurados"""
        self._reset_daily_limits()
        all_jobs = []
        
        for portal in filters.portals:
            if self.current_counts[portal] >= self.daily_limits[portal]:
                logger.info(f"Límite diario alcanzado para {portal}")
                continue
            
            try:
                if portal == JobPortal.LINKEDIN:
                    jobs = await self._scrape_linkedin(filters)
                elif portal == JobPortal.LABORUM:
                    jobs = await self._scrape_laborum(filters)
                elif portal == JobPortal.BNE:
                    jobs = await self._scrape_bne(filters)
                elif portal == JobPortal.TRABAJANDO:
                    jobs = await self._scrape_trabajando(filters)
                else:
                    jobs = []
                
                all_jobs.extend(jobs)
                self.current_counts[portal] += len(jobs)
                
                logger.info(f"Encontrados {len(jobs)} trabajos en {portal}")
                
                # Delay entre portales
                await self._human_delay(10, 20)
                
            except Exception as e:
                logger.error(f"Error scrapeando {portal}: {e}")
                continue
        
        return all_jobs
    
    async def _scrape_linkedin(self, filters: SearchFilters) -> List[JobPosting]:
        """Scraper para LinkedIn"""
        jobs = []
        driver = None
        
        try:
            driver = self._get_chrome_driver()
            
            # Construir URL de búsqueda
            keywords = " ".join(filters.keywords)
            location = filters.locations[0] if filters.locations else "Santiago, Chile"
            
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}"
            
            driver.get(search_url)
            await self._human_delay(3, 6)
            
            # Obtener lista de trabajos
            job_cards = driver.find_elements(By.CSS_SELECTOR, "[data-job-id]")
            
            for card in job_cards[:self.daily_limits[JobPortal.LINKEDIN]]:
                try:
                    job_id = card.get_attribute("data-job-id")
                    title_element = card.find_element(By.CSS_SELECTOR, "h3 a")
                    company_element = card.find_element(By.CSS_SELECTOR, "[data-tracking-control-name='public_jobs_jserp-result_job-search-card-subtitle']")
                    location_element = card.find_element(By.CSS_SELECTOR, "[data-tracking-control-name='public_jobs_jserp-result_job-search-card-location']")
                    
                    job = JobPosting(
                        portal=JobPortal.LINKEDIN,
                        external_id=job_id,
                        url=title_element.get_attribute("href"),
                        title=title_element.text.strip(),
                        company=company_element.text.strip(),
                        location=location_element.text.strip(),
                        description="",  # Se llenará después
                        requirements=[],
                        keywords_matched=self._find_matching_keywords(title_element.text, filters.keywords)
                    )
                    
                    jobs.append(job)
                    await self._human_delay(1, 3)
                    
                except Exception as e:
                    logger.warning(f"Error procesando trabajo LinkedIn: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error general LinkedIn: {e}")
        
        finally:
            if driver:
                driver.quit()
        
        return jobs
    
    async def _scrape_laborum(self, filters: SearchFilters) -> List[JobPosting]:
        """Scraper para Laborum/Trabajando.com"""
        jobs = []
        
        try:
            keywords = "+".join(filters.keywords)
            location = filters.locations[0] if filters.locations else "Santiago"
            
            search_url = f"https://www.trabajando.com/trabajo-empleo/{keywords}/{location}"
            
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = self.session.get(search_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            job_cards = soup.find_all('div', class_=['job-item', 'job-card'])
            
            for card in job_cards[:self.daily_limits[JobPortal.LABORUM]]:
                try:
                    title_elem = card.find('h3') or card.find('a', class_='job-title')
                    company_elem = card.find(class_=['company-name', 'empresa'])
                    location_elem = card.find(class_=['location', 'ubicacion'])
                    
                    if not title_elem:
                        continue
                    
                    # Extraer URL
                    link_elem = title_elem.find('a') or card.find('a')
                    job_url = link_elem.get('href') if link_elem else ""
                    if job_url and not job_url.startswith('http'):
                        job_url = "https://www.trabajando.com" + job_url
                    
                    job = JobPosting(
                        portal=JobPortal.LABORUM,
                        external_id=job_url.split('/')[-1] if job_url else str(random.randint(10000, 99999)),
                        url=job_url,
                        title=title_elem.get_text(strip=True),
                        company=company_elem.get_text(strip=True) if company_elem else "No especificado",
                        location=location_elem.get_text(strip=True) if location_elem else location,
                        description="",
                        requirements=[],
                        keywords_matched=self._find_matching_keywords(title_elem.get_text(), filters.keywords)
                    )
                    
                    jobs.append(job)
                    
                except Exception as e:
                    logger.warning(f"Error procesando trabajo Laborum: {e}")
                    continue
            
            await self._human_delay(3, 8)
        
        except Exception as e:
            logger.error(f"Error general Laborum: {e}")
        
        return jobs
    
    async def _scrape_bne(self, filters: SearchFilters) -> List[JobPosting]:
        """Scraper para Bolsa Nacional de Empleo (BNE)"""
        jobs = []
        
        try:
            # BNE API o scraping
            keywords = " ".join(filters.keywords)
            
            # URL de búsqueda BNE
            search_url = f"https://www.bne.cl/buscar-trabajo?q={keywords}"
            
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = self.session.get(search_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Buscar elementos de trabajo (ajustar selectores según BNE actual)
                job_elements = soup.find_all('div', class_=['trabajo', 'empleo-item'])
                
                for element in job_elements[:self.daily_limits[JobPortal.BNE]]:
                    try:
                        title_elem = element.find('h3') or element.find('a', class_='titulo')
                        company_elem = element.find(class_='empresa')
                        
                        if not title_elem:
                            continue
                        
                        job = JobPosting(
                            portal=JobPortal.BNE,
                            external_id=str(random.randint(10000, 99999)),
                            url=search_url,
                            title=title_elem.get_text(strip=True),
                            company=company_elem.get_text(strip=True) if company_elem else "Empleador BNE",
                            location="Chile",
                            description="",
                            requirements=[],
                            keywords_matched=self._find_matching_keywords(title_elem.get_text(), filters.keywords)
                        )
                        
                        jobs.append(job)
                        
                    except Exception as e:
                        logger.warning(f"Error procesando trabajo BNE: {e}")
                        continue
            
            await self._human_delay(3, 8)
        
        except Exception as e:
            logger.error(f"Error general BNE: {e}")
        
        return jobs
    
    async def _scrape_trabajando(self, filters: SearchFilters) -> List[JobPosting]:
        """Scraper adicional para Trabajando.com con diferentes estrategia"""
        jobs = []
        
        try:
            # Implementación similar a Laborum pero con diferentes selectores
            # Para evitar duplicados, usar una estrategia diferente o portal diferente
            
            keywords = "%20".join(filters.keywords)
            search_url = f"https://cl.trabajando.com/trabajo-empleo-de-{keywords}"
            
            headers = {
                'User-Agent': self.ua.random,
                'Referer': 'https://cl.trabajando.com/'
            }
            
            response = self.session.get(search_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Selectores específicos para trabajando.com
                job_cards = soup.find_all('div', class_=['oferta', 'trabajo-card'])
                
                for card in job_cards[:self.daily_limits[JobPortal.TRABAJANDO]]:
                    try:
                        title_elem = card.find('h2') or card.find(class_='titulo-oferta')
                        company_elem = card.find(class_=['nombre-empresa', 'company'])
                        
                        if not title_elem:
                            continue
                        
                        job = JobPosting(
                            portal=JobPortal.TRABAJANDO,
                            external_id=str(random.randint(20000, 99999)),
                            url=search_url,
                            title=title_elem.get_text(strip=True),
                            company=company_elem.get_text(strip=True) if company_elem else "Empresa",
                            location="Santiago, Chile",
                            description="",
                            requirements=[],
                            keywords_matched=self._find_matching_keywords(title_elem.get_text(), filters.keywords)
                        )
                        
                        jobs.append(job)
                        
                    except Exception as e:
                        logger.warning(f"Error procesando trabajo Trabajando.com: {e}")
                        continue
            
            await self._human_delay(3, 8)
            
        except Exception as e:
            logger.error(f"Error general Trabajando.com: {e}")
        
        return jobs
    
    def _find_matching_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """Encontrar keywords que coinciden en el texto"""
        text_lower = text.lower()
        matched = []
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matched.append(keyword)
        
        return matched
    
    async def search_and_apply(self, user_id: str):
        """Proceso completo de búsqueda y postulación para un usuario"""
        try:
            logger.info(f"Iniciando búsqueda automática para usuario {user_id}")
            
            # TODO: Obtener filtros de usuario desde DB
            # TODO: Buscar trabajos
            # TODO: Filtrar trabajos ya postulados
            # TODO: Aplicar automáticamente con límites de velocidad
            
            logger.info(f"Búsqueda completada para usuario {user_id}")
            
        except Exception as e:
            logger.error(f"Error en búsqueda automática para usuario {user_id}: {e}")