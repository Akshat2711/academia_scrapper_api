import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
import os
from dotenv import load_dotenv
load_dotenv()



class SRMPortalScraper:
    """Simple SRM Student Portal scraper that returns structured data"""
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
    
    async def scrape_data(self) -> dict:
        """Main method to scrape and return all data as dictionary"""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        try:
            # Login
            await page.goto("https://academia.srmist.edu.in/", wait_until="networkidle")
            iframe = page.frame_locator(".siginiframe")
            await iframe.locator("input#login_id").fill(self.email)
            await iframe.locator("#nextbtn").click()
            await iframe.locator("input#password").fill(self.password)
            await iframe.locator("#nextbtn").click()
            await page.wait_for_timeout(3000)
            
            # Navigate to attendance
            await page.click("#tab_My_Time_Table_Attendance")
            await page.click("#My_Attendance")
            await page.wait_for_selector(".mainDiv", state="attached")
            await page.locator(".mainDiv").scroll_into_view_if_needed()
            await page.wait_for_timeout(2000)
            
            # Extract and parse HTML
            html_content = await page.locator(".mainDiv").inner_html()
            data = self._parse_all_data(html_content)
            
            return data
            
        finally:
            await browser.close()
            await playwright.stop()
    
    def _parse_all_data(self, html_content: str) -> dict:
        """Parsing   data and returning as structured dictionary"""
        soup = BeautifulSoup(html_content, 'html.parser')
        tables = soup.find_all('table')
        
        return {
            'student_info': self._parse_student_info(tables[1]),
            'attendance': self._parse_attendance(tables[2]),
            'marks': self._parse_marks(tables[3]),
            'summary': {}  # Will be populated after parsing
        }
    
    def _parse_student_info(self, table) -> dict:
        """Parse student basic information"""
        info = {}
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True).rstrip(':').lower().replace(' ', '_')
                if key == 'photo-id':
                    img_tag = cells[1].find('img')
                    info['photo_url'] = img_tag['src'] if img_tag else ""
                else:
                    value = cells[1].get_text(strip=True)
                    info[key] = value
        
        # Clean up enrollment data
        if 'enrollment_status_/_doe' in info:
            enrollment = info.pop('enrollment_status_/_doe')
            if ' / ' in enrollment:
                info['enrollment_status'], info['enrollment_date'] = enrollment.split(' / ')
            else:
                info['enrollment_status'] = enrollment
                info['enrollment_date'] = ""
        
        return info
    
    def _parse_attendance(self, table) -> dict:
        """Parse attendance data"""
        attendance = {}
        rows = table.find_all('tr')[1:]  # Skip header
        
        total_conducted = 0
        total_absent = 0
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 9:
                course_code = cells[0].get_text(strip=True).split('\n')[0]
                
                hours_conducted = int(cells[6].get_text(strip=True))
                hours_absent = int(cells[7].get_text(strip=True))
                att_text = cells[8].get_text(strip=True)
                att_percentage = float(re.findall(r'\d+\.\d+', att_text)[0]) if re.findall(r'\d+\.\d+', att_text) else 0.0
                
                attendance[course_code] = {
                    'course_title': cells[1].get_text(strip=True),
                    'category': cells[2].get_text(strip=True),
                    'faculty_name': cells[3].get_text(strip=True),
                    'slot': cells[4].get_text(strip=True),
                    'room_no': cells[5].get_text(strip=True),
                    'hours_conducted': hours_conducted,
                    'hours_absent': hours_absent,
                    'attendance_percentage': att_percentage
                }
                
                total_conducted += hours_conducted
                total_absent += hours_absent
        
        # Add overall attendance
        overall_percentage = round(((total_conducted - total_absent) / total_conducted) * 100, 2) if total_conducted > 0 else 0.0
        
        return {
            'courses': attendance,
            'overall_attendance': overall_percentage,
            'total_hours_conducted': total_conducted,
            'total_hours_absent': total_absent
        }
    
    def _parse_marks(self, table) -> dict:
        """Parse marks data"""
        marks = {}
        rows = table.find_all('tr')[1:]  # Skip header
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 3:
                course_code = cells[0].get_text(strip=True)
                course_type = cells[1].get_text(strip=True)
                
                tests = []
                nested_table = cells[2].find('table')
                if nested_table:
                    font_tags = nested_table.find_all('font')
                    for font_tag in font_tags:
                        font_html = str(font_tag)
                        
                        if '<br' in font_html and '/' in font_html:
                            try:
                                strong_tag = font_tag.find('strong')
                                if strong_tag:
                                    strong_text = strong_tag.get_text(strip=True)
                                    if '/' in strong_text:
                                        test_name, max_marks_str = strong_text.split('/')
                                        max_marks = float(max_marks_str.strip())
                                        
                                        # Extract obtained marks after <br>
                                        br_split = font_html.split('<br')
                                        if len(br_split) > 1:
                                            after_br = br_split[1].split('>', 1)[1] if '>' in br_split[1] else br_split[1]
                                            obtained_text = after_br.replace('</font>', '').strip()
                                            
                                            if obtained_text:
                                                obtained_marks = float(obtained_text)
                                                tests.append({
                                                    'test_name': test_name.strip(),
                                                    'obtained_marks': obtained_marks,
                                                    'max_marks': max_marks,
                                                    'percentage': round((obtained_marks / max_marks) * 100, 2)
                                                })
                            except (ValueError, IndexError, AttributeError):
                                continue
                
                marks[course_code] = {
                    'course_type': course_type,
                    'tests': tests
                }
        
        return marks




#calling function
async def get_srm_data(email: str, password: str) -> dict:
    """Get SRM student data as dictionary"""
    scraper = SRMPortalScraper(email, password)
    return await scraper.scrape_data()










# Main execution
async def main():
    email = os.getenv("SRM_EMAIL")
    password = os.getenv("SRM_PASSWORD")
    
    # Get all data
    data = await get_srm_data(email, password)
    
    # Print complete data dictionary
    print("\n" + "="*50)
    print("COMPLETE STUDENT DATA")
    print("="*50)
    
    import json
    print(json.dumps(data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())