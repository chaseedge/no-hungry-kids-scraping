import os
from scrapers.idaho import Idaho
from scrapers.delaware import Delaware
from scrapers.usda_fns import scrape_and_save as scrape_usda
from settings import report_cols

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

scrapers_dict = {"idaho": Idaho,
                 "delaware": Delaware}

def get_report_format_type():
    file_fmt = input("Select state data file type? [csv]/xlsx/json  ").strip().lower()
    file_fmt = file_fmt if file_fmt else "csv"
    if file_fmt not in ["csv","xlsx","json"]:
        return
    else:
        return file_fmt

def save(scraper, state_name):
    df = scraper().scrape()
    fn = os.path.join(DATA_DIR, f"{state_name}.xlsx")
    df[report_cols].to_excel(fn, index=False)

    fn = os.path.join(DATA_DIR, f"{state_name}.csv")
    df[report_cols].to_csv(fn, index=False)

    fn = os.path.join(DATA_DIR, f"{state_name}.json")
    df[report_cols].to_json(fn, orient="records")

def main():
    for state_name, scraper in scrapers_dict.items():
        update = input(f"Update {state_name.capitalize()}? y/[N] ").strip().lower()
        if update == "y":
            save(scraper, state_name)

    update_usda = input("Update USDA FNS contacts json file? y/[N]").strip().lower()
    if update_usda == "y":
        scrape_usda(os.path.join(DATA_DIR, "usda_fns_contacts.json"))

if __name__ == "__main__":
    main()