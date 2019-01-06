import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import csv

# Scrolls to the bottom of the page to load more recipes
def scroll(driver):
	SCROLL_PAUSE_TIME = 2.0

	for i in range(0,6):
		driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
		sleep(SCROLL_PAUSE_TIME)

# Returns the recipe links from the url passed in representing a category of cuisine
def get_recipe_links(driver, url):
    recipies = []
    print('Getting recipe links from %s' % url)

    try:
    	driver.get(url)
    	scroll(driver)
    	sleep(2)
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        links = soup.select('.fixed-recipe-card__h3 a')
        for link in links:
        	recipe = link['href']
        	recipies.append(recipe)
    except Exception as ex:
        print('Exception in get_recipes')
        print(str(ex))
    finally:
        return recipies

# Retrieves the recipe information from the recipe card and tags them with the corresponding cuisine
def get_recipe_information(driver, recipe_id, recipe_tag):
	information = []
	print('Getting Recipe Information')
	try:
		title = driver.find_element_by_class_name('recipe-summary__h1').text
		rating_html = driver.find_element_by_class_name('recipe-summary__stars').get_attribute('innerHTML')
	
	# Want to only get the recipe ratingns instead of the reviews
		soup = BeautifulSoup(rating_html, 'lxml')
		rating = soup.find('meta', itemprop="ratingValue")['content']
		total_reviews = soup.find('meta', itemprop="reviewCount")['content']
		ingredients_elements = driver.find_elements_by_class_name('recipe-ingred_txt')
		# Last element is always a point stating if you want to add the time to the list
		ingredients = [element.text.encode('ascii', 'ignore').decode('ascii') for element in ingredients_elements]
		ingredients.pop()

		nutrition_html = driver.find_element_by_class_name('nutrition-summary-facts').get_attribute('innerHTML')
		nutrition_soup = BeautifulSoup(nutrition_html, 'lxml')
		calories = nutrition_soup.find('span', itemprop='calories').text.split(' ')[0] #
		carbs = nutrition_soup.find('span', itemprop='carbohydrateContent').text #g
		protein = nutrition_soup.find('span', itemprop='proteinContent').text #g
		cholesterol = nutrition_soup.find('span', itemprop='cholesterolContent').text #mg
		sodiumContent = nutrition_soup.find('span', itemprop='sodiumContent').text #mg

		return (recipe_id, recipe_tag, title, rating, total_reviews, ingredients, calories, carbs, protein, cholesterol, sodiumContent)
	except Exception as EX:
		print('Exception in get_recipe_information')
		return None


# Retrieves user reviews from the url maximum retrieved is always 30
def get_user_reviews(driver, recipe_id):
	print("Getting user reviews")
	reviews = []
	review_links = driver.find_elements_by_class_name('review-detail__link')
	review_counts = 0
	try:
		review_links[0].click()
		sleep(2.0)
		footer = driver.find_element_by_css_selector("div[class='footer noselect']").get_attribute("innerHTML")
		soup = BeautifulSoup(footer, 'lxml')
		total_reviews = soup.find_all('span')[1].text	
		review_counts = total_reviews if total_reviews < 30 else 30

	except Exception as ex:
		print('Encountered the annoying pop-up')
		sleep(2.0)
		driver.find_element_by_class_name('acsDeclineButton').click()
		review_links[0].click()

	for i in range(1, review_counts):
		try:
			review_text = driver.find_element_by_class_name('ReviewText').text.encode('ascii', 'ignore').decode('ascii')
			reviews.append([recipe_id, review_text])
			driver.find_element_by_id('BI_loadReview2_right').click()
			sleep(1)
		except Exception as ex:
			print('exception thrown in get_user_reviews')
			print(str(ex))
			sleep(1)
			driver.find_element_by_id('BI_loadReview2_right').click()

	return reviews


if __name__ == '__main__':
	urls = ["https://www.allrecipes.com/recipes/723/world-cuisine/european/italian",
	"https://www.allrecipes.com/recipes/726/world-cuisine/european/spanish",
	"https://www.allrecipes.com/recipes/731/world-cuisine/european/greek",
	"https://www.allrecipes.com/recipes/721/world-cuisine/european/french",
	"https://www.allrecipes.com/recipes/722/world-cuisine/european/german",
	"https://www.allrecipes.com/recipes/724/world-cuisine/european/portuguese",
	"https://www.allrecipes.com/recipes/695/world-cuisine/asian/chinese",
	"https://www.allrecipes.com/recipes/702/world-cuisine/asian/thai",
	"https://www.allrecipes.com/recipes/233/world-cuisine/asian/indian",
	"https://www.allrecipes.com/recipes/728/world-cuisine/latin-american/mexican",
	"https://www.allrecipes.com/recipes/700/world-cuisine/asian/korean",
	"https://www.allrecipes.com/recipes/699/world-cuisine/asian/japanese",
	"https://www.allrecipes.com/recipes/703/world-cuisine/asian/vietnamese",
	"https://www.allrecipes.com/recipes/230/world-cuisine/latin-american/caribbean/jamaican",
	"https://www.allrecipes.com/recipes/709/world-cuisine/latin-american/caribbean/cuban"]
	driver = webdriver.Firefox()
	index = 0
	for url in urls:
		links = get_recipe_links(driver, url)
		print("Amount of links for this url %d" % len(links))

		for recipe in links:
			driver.get(recipe)
			tag = url.split("/")[-1]
			recipe_information = get_recipe_information(driver, index, tag)
			if recipe_information is None:
				continue

			with open("recipes.csv", "a") as f:
				writer = csv.writer(f)
				writer.writerow(recipe_information)

			with open("reviews.csv", "a") as f:
				review_writer = csv.writer(f)
				review_writer.writerows(get_user_reviews(driver, index))		
			index += 1		
	
