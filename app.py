import os
from scrapers.idaho import Idaho
from scrapers.usda_fns import scrape_and_save as scrape_usda
from settings import report_cols

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

scrapers_dict = {"idaho": Idaho}

def get_report_format_type():
    file_fmt = input("Select state data file type? [csv]/xlsx/json  ").strip().lower()
    file_fmt = file_fmt if file_fmt else "csv"
    if file_fmt not in ["csv","xlsx","json"]:
        return
    else:
        return file_fmt

def save(scraper, state_name, file_fmt):
    df = scraper().scrape()
    if file_fmt == "xlsx":
        fn = os.path.join(DATA_DIR, f"{state_name}.xlsx")
        df[report_cols].to_excel(fn, index=False)
    elif file_fmt == "csv":
        fn = os.path.join(DATA_DIR, f"{state_name}.csv")
        df[report_cols].to_csv(fn, index=False)
    else:
        fn = os.path.join(DATA_DIR, f"{state_name}.json")
        df[report_cols].to_json(fn, orient="records")

def main():
    file_fmt = get_report_format_type()
    if not file_fmt:
        print("%s is not a valid option, try again")
        file_fmt = get_report_format_type()
    if not file_fmt:
        print("Incorrect again")
        exit()

    update_idaho = input("Update Idaho? y/[N] ").strip().lower()
    if update_idaho == "y":
        save(Idaho, "idaho", file_fmt)

    update_usda = input("Update USDA FNS contacts json file? y/[N]").strip().lower()
    if update_usda == "y":
        scrape_usda(os.path.join(DATA_DIR, "usda_fns_contacts.json"))

if __name__ == "__main__":
    main()