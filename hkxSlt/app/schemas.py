from marshmallow import Schema, fields, post_load
from app.models import User, Building, Apartment, Owner, Service, Charge, Payment, Request, Staff, Expense, Resident


class UserSchema(Schema):
      id = fields.Int(dump_only=True)
      username = fields.Str(required=True)
      role = fields.Str(default='User')
      blocked = fields.Bool(default=False)

      @post_load
      def make_user(self, data, **kwargs):
          return User(**data)


class BuildingSchema(Schema):
      id = fields.Int(dump_only=True)
      address = fields.Str(required=True)
      start_management_date = fields.DateTime(format='%Y-%m-%dT%H:%M:%SZ')
      floors = fields.Int()
      year_built = fields.Int()
      total_area = fields.Decimal(as_string=True)
      city = fields.Str()
      street = fields.Str()
      house_number = fields.Str()

      @post_load
      def make_building(self, data, **kwargs):
          return Building(**data)


class ApartmentSchema(Schema):
      id = fields.Int(dump_only=True)
      number = fields.Int(required=True)
      area = fields.Decimal(as_string=True)
      building_id = fields.Int(required=True)
      owner_id = fields.Int(allow_none=True)

      @post_load
      def make_apartment(self, data, **kwargs):
          return Apartment(**data)


class OwnerSchema(Schema):
      id = fields.Int(dump_only=True)
      full_name = fields.Str(required=True)
      phone = fields.Str(required=True)
      email = fields.Email(allow_none=True)

      @post_load
      def make_owner(self, data, **kwargs):
          return Owner(**data)


class ServiceSchema(Schema):
      id = fields.Int(dump_only=True)
      name = fields.Str(required=True)

      @post_load
      def make_service(self, data, **kwargs):
          return Service(**data)


class ChargeSchema(Schema):
      id = fields.Int(dump_only=True)
      apartment_id = fields.Int(required=True)
      service_id = fields.Int(required=True)
      period = fields.Str(required=True)
      amount = fields.Decimal(as_string=True)

      @post_load
      def make_charge(self, data, **kwargs):
          return Charge(**data)


class PaymentSchema(Schema):
      id = fields.Int(dump_only=True)
      apartment_id = fields.Int(required=True)
      service_id = fields.Int(required=True)
      paid_amount = fields.Decimal(as_string=True)
      payment_date = fields.DateTime(format='%Y-%m-%dT%H:%M:%SZ', allow_none=True)

      @post_load
      def make_payment(self, data, **kwargs):
          return Payment(**data)


class RequestSchema(Schema):
      id = fields.Int(dump_only=True)
      title = fields.Str(required=True)
      description = fields.Str(required=True)
      status = fields.Str(required=True)
      priority = fields.Str(required=True)
      apartment_id = fields.Int(required=True)

      @post_load
      def make_request(self, data, **kwargs):
          return Request(**data)


class StaffSchema(Schema):
      id = fields.Int(dump_only=True)
      first_name = fields.Str(required=True)
      last_name = fields.Str(required=True)
      position = fields.Str(required=True)
      phone = fields.Str(required=True)
      email = fields.Email(required=True)

      @post_load
      def make_staff(self, data, **kwargs):
          return Staff(**data)


class ExpenseSchema(Schema):
      id = fields.Int(dump_only=True)
      date = fields.DateTime(format='%Y-%m-%dT%H:%M:%SZ', required=True)
      amount = fields.Decimal(as_string=True, required=True)
      description = fields.Str(required=True)
      category = fields.Str(required=True)

      @post_load
      def make_expense(self, data, **kwargs):
          return Expense(**data)


class ResidentSchema(Schema):
      id = fields.Int(dump_only=True)
      name = fields.Str(required=True)
      phone = fields.Str(required=True)
      email = fields.Email(allow_none=True)
      relation_to_owner = fields.Str(required=True)
      apartment_id = fields.Int(required=True)

      @post_load
      def make_resident(self, data, **kwargs):
          return Resident(**data)