class TerritoryManager:
    def __init__(self, employees, customers, territories, assignments):
        self.employees = {e.employee_id: e for e in employees}
        self.customers = customers
        self.territories = {t.territory_id: t for t in territories}
        self.assignments = assignments

        # mapping email → list territory
        self.email_territory_map = {}
        for a in assignments:
            self.email_territory_map.setdefault(a.email, []).append(a.territory_id)

    def is_customer_correctly_assigned(self, customer):
        emp = self.employees.get(customer.emp_id)

        if not emp or not emp.is_active():
            return False

        territory_ids = self.email_territory_map.get(emp.email, [])

        for t_id in territory_ids:
            territory = self.territories.get(t_id)
            if (
                territory.province.strip().upper() == customer.province.strip().upper()
                and territory.ward.strip().upper() == customer.ward.strip().upper()
            ):
                return True

        return False

    def get_wrong_assignments(self):
        wrong_list = []

        for customer in self.customers:
            if not self.is_customer_correctly_assigned(customer):
                wrong_list.append(customer)

        return wrong_list