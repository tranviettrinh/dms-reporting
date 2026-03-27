class Employee:
    def __init__(
        self,
        employee_id,
        employee_name,
        employee_phone=None,
        employee_unit=None,
        employee_status=None,
        employee_type=None,
        employee_birthday=None,
        employee_mail=None,
        employee_gmail=None,
        employee_startday=None,
        employee_enday=None,
    ):
        self.employee_id = employee_id
        self.employee_name = employee_name
        self.employee_phone = employee_phone
        self.employee_unit = employee_unit
        self.employee_status = employee_status
        self.employee_type = employee_type
        self.employee_birthday = employee_birthday
        self.employee_mail = employee_mail
        self.employee_gmail = employee_gmail
        self.employee_startday = employee_startday
        self.employee_enday = employee_enday
        self.customers = []

    def add_customer(self, customer):
        if customer not in self.customers:
            self.customers.append(customer)
    def is_active(self):
        return self.employee_status == "Đang làm việc"

    def __repr__(self):
        return f"Employee({self.employee_id}, {self.employee_name})"