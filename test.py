from db.companies.companies_schema import get_central_connection, create_central_tables
from db.companies.companies_repo import fetch_all_companies
from services.companies.company_service import CompanyService

# اتصال بـ companies.db
central_conn = get_central_connection()
create_central_tables(central_conn)

# جيب الشركات
companies = fetch_all_companies(central_conn)
print("Companies:", [(c["id"], c["name"]) for c in companies])

if companies:
    c = companies[0]
    # عيّن الشركة النشطة بالـ signature الصح
    CompanyService.set_active_company(c["id"], c["name"], c["color"] or "#1565c0")
    
    conn = CompanyService.get_active_erp_conn()
    print("conn:", conn)
    
    from ui.tabs.costing.product._catalog_provider import build_product_catalog
    catalog = build_product_catalog(conn)
    print("raw:", len(catalog.get("raw", [])))
    print("semi:", len(catalog.get("semi", [])))
    print("labor_op:", len(catalog.get("labor_op", [])))
    print("machine_op:", len(catalog.get("machine_op", [])))