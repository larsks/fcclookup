from typing import override
from collections.abc import Iterable

import datetime
import csv

from sqlalchemy import create_engine
from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import inspect
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session
from sqlalchemy.orm import validates


def validate_date_field(
    name: str, value: str | datetime.date | None
) -> datetime.date | None:
    if isinstance(value, datetime.date):
        return value
    elif value is None:
        return None
    elif isinstance(value, str):
        if value == "":
            return None
        else:
            month, day, year = [int(x) for x in value.split("/")]
            return datetime.date(year=year, month=month, day=day)
    else:
        raise ValueError(
            f"invalid date: '{value}': date value must be a datetime.date object or a string of the form mm/dd/yyyy"
        )


class uls_dialect(csv.Dialect):
    delimiter = "|"
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = "\r\n"
    quoting = (
        csv.QUOTE_NONE
    )  # needed to deal with some screwed up quoting in FCC source data


csv.register_dialect("uls", uls_dialect)


class Base(DeclarativeBase):
    @classmethod
    def get_field_names(cls) -> list[str]:
        mapper = inspect(cls)
        return [field.name for field in mapper.c if not field.name.startswith("_")]

    @classmethod
    def import_csv(cls, data: Iterable[str], session: Session, delimiter: str = "|"):
        def line_combiner(data: Iterable[str]) -> Iterable[str]:
            """Deal with weird quoting in ULS source files.

            Fields in ULS source files are unquoted, but in some cases contained embedded carriage returns. To
            avoid problems, we need to (a) disable universal newlines when opening the files, and (b) we need
            to identify terminal carriage returns as line-continuation characters, and (c) we need to replace
            them with another character to keep the csv module happy."""

            vline: list[str] = []
            for line in data:
                # strip '\r\n' from end of line
                line = line.removesuffix("\r\n")
                vline.append(line.replace("\r", " "))
                if line.endswith("\r"):
                    continue
                yield "".join(vline)
                vline = []

        fieldnames = cls.get_field_names()
        reader = csv.DictReader(
            line_combiner(data), fieldnames=fieldnames, dialect="uls"
        )
        for row in reader:
            obj = cls(**row)
            session.add(obj)

    @override
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"{','.join([f'{key}={self.__dict__[key]!r}' for key in self.get_field_names() if key in self.__dict__])}"
            ")"
        )


class Entity(Base):
    __tablename__: str = "entity"

    record_type: Mapped[str] = mapped_column(String(2), nullable=False)
    unique_system_identifier: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        primary_key=True,
    )
    uls_file_number: Mapped[str] = mapped_column(String(4), nullable=True)
    ebf_number: Mapped[str] = mapped_column(String(30), nullable=True)
    call_sign: Mapped[str] = mapped_column(String(10), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(2), nullable=True)
    licensee_id: Mapped[str] = mapped_column(String(9), nullable=True)
    entity_name: Mapped[str] = mapped_column(String(200), nullable=True)
    first_name: Mapped[str] = mapped_column(String(20), nullable=True)
    mi: Mapped[str] = mapped_column(String(1), nullable=True)
    last_name: Mapped[str] = mapped_column(String(20), nullable=True)
    suffix: Mapped[str] = mapped_column(String(3), nullable=True)
    phone: Mapped[str] = mapped_column(String(10), nullable=True)
    fax: Mapped[str] = mapped_column(String(10), nullable=True)
    email: Mapped[str] = mapped_column(String(50), nullable=True)
    street_address: Mapped[str] = mapped_column(String(60), nullable=True)
    city: Mapped[str] = mapped_column(String(20), nullable=True)
    state: Mapped[str] = mapped_column(String(2), nullable=True)
    zip_code: Mapped[str] = mapped_column(String(9), nullable=True)
    po_box: Mapped[str] = mapped_column(String(20), nullable=True)
    attention_line: Mapped[str] = mapped_column(String(35), nullable=True)
    sgin: Mapped[str] = mapped_column(String(3), nullable=True)
    fcc_registration_number: Mapped[str] = mapped_column(String(10), nullable=True)
    applicant_type_code: Mapped[str] = mapped_column(String(1), nullable=True)
    applicant_type_code_other: Mapped[str] = mapped_column(String(40), nullable=True)
    status_code: Mapped[str] = mapped_column(String(1), nullable=True)
    status_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    ghz_license_type: Mapped[str] = mapped_column(String(1), nullable=True)
    linked_unique_system_identifier: Mapped[int] = mapped_column(Integer, nullable=True)
    linked_call_sign: Mapped[str] = mapped_column(String(10), nullable=True)

    license: Mapped[list["Amateur"]] = relationship()
    history: Mapped[list["History"]] = relationship()
    headers: Mapped[list["LicenseHeader"]] = relationship()
    attachments: Mapped[list["LicenseAttachment"]] = relationship()
    comments: Mapped[list["Comment"]] = relationship()
    special_conditions: Mapped[list["LicenseSpecialCondition"]] = relationship()
    freeform_special_conditions: Mapped[list["LicenseFreeformSpecialCondition"]] = (
        relationship()
    )

    @validates("status_date")
    def validate_status_date(
        self, name: str, value: str | datetime.date
    ) -> datetime.date | None:
        return validate_date_field(name, value)


class Amateur(Base):
    __tablename__: str = "amateur"

    record_type: Mapped[str] = mapped_column(String(2), nullable=False)
    unique_system_identifier: Mapped[int] = mapped_column(
        ForeignKey("entity.unique_system_identifier"),
        primary_key=True,
    )
    uls_file_number: Mapped[str] = mapped_column(String(14), nullable=True)
    ebf_number: Mapped[str] = mapped_column(String(30), nullable=True)
    call_sign: Mapped[str] = mapped_column(String(10), nullable=True)
    operator_class: Mapped[str] = mapped_column(String(1), nullable=True)
    group_code: Mapped[str] = mapped_column(String(1), nullable=True)
    region_code: Mapped[int] = mapped_column(Integer)
    trustee_call_sign: Mapped[str] = mapped_column(String(10), nullable=True)
    trustee_indicator: Mapped[str] = mapped_column(String(1), nullable=True)
    physician_certification: Mapped[str] = mapped_column(String(1), nullable=True)
    ve_signature: Mapped[str] = mapped_column(String(1), nullable=True)
    systematic_call_sign_change: Mapped[str] = mapped_column(String(1), nullable=True)
    vanity_call_sign_change: Mapped[str] = mapped_column(String(1), nullable=True)
    vanity_relationship: Mapped[str] = mapped_column(String(12), nullable=True)
    previous_call_sign: Mapped[str] = mapped_column(String(10), nullable=True)
    previous_operator_class: Mapped[str] = mapped_column(String(1), nullable=True)
    trustee_name: Mapped[str] = mapped_column(String(50), nullable=True)


class History(Base):
    __tablename__: str = "history"

    record_type: Mapped[str] = mapped_column(String(2), nullable=False)
    unique_system_identifier: Mapped[int] = mapped_column(
        ForeignKey("entity.unique_system_identifier"),
    )
    uls_file_number: Mapped[str] = mapped_column(String(14), nullable=True)
    call_sign: Mapped[str] = mapped_column(String(10), nullable=True)
    log_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    code: Mapped[str] = mapped_column(String(6), nullable=True)
    _id: Mapped[int] = mapped_column(Integer, primary_key=True)

    @validates("log_date")
    def validate_log_date(
        self, name: str, value: str | datetime.date
    ) -> datetime.date | None:
        return validate_date_field(name, value)


class LicenseHeader(Base):
    __tablename__: str = "license_header"

    record_type: Mapped[str] = mapped_column(String(2), nullable=False)
    unique_system_identifier: Mapped[int] = mapped_column(
        ForeignKey("entity.unique_system_identifier"),
        primary_key=True,
    )
    uls_file_number: Mapped[str] = mapped_column(String(14), nullable=True)
    ebf_number: Mapped[str] = mapped_column(String(30), nullable=True)
    call_sign: Mapped[str] = mapped_column(String(10), nullable=True)
    license_status: Mapped[str] = mapped_column(String(1), nullable=True)
    radio_service_code: Mapped[str] = mapped_column(String(2), nullable=True)
    grant_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    expired_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    cancellation_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    eligibility_rule_num: Mapped[str] = mapped_column(String(10), nullable=True)
    applicant_type_code_reserved: Mapped[str] = mapped_column(String(1), nullable=True)
    alien: Mapped[str] = mapped_column(String(1), nullable=True)
    alien_government: Mapped[str] = mapped_column(String(1), nullable=True)
    alien_corporation: Mapped[str] = mapped_column(String(1), nullable=True)
    alien_officer: Mapped[str] = mapped_column(String(1), nullable=True)
    alien_control: Mapped[str] = mapped_column(String(1), nullable=True)
    revoked: Mapped[str] = mapped_column(String(1), nullable=True)
    convicted: Mapped[str] = mapped_column(String(1), nullable=True)
    adjudged: Mapped[str] = mapped_column(String(1), nullable=True)
    involved_reserved: Mapped[str] = mapped_column(String(1), nullable=True)
    common_carrier: Mapped[str] = mapped_column(String(1), nullable=True)
    non_common_carrier: Mapped[str] = mapped_column(String(1), nullable=True)
    private_comm: Mapped[str] = mapped_column(String(1), nullable=True)
    fixed: Mapped[str] = mapped_column(String(1), nullable=True)
    mobile: Mapped[str] = mapped_column(String(1), nullable=True)
    radiolocation: Mapped[str] = mapped_column(String(1), nullable=True)
    satellite: Mapped[str] = mapped_column(String(1), nullable=True)
    developmental_or_sta: Mapped[str] = mapped_column(String(1), nullable=True)
    interconnected_service: Mapped[str] = mapped_column(String(1), nullable=True)
    certifier_first_name: Mapped[str] = mapped_column(String(20), nullable=True)
    certifier_mi: Mapped[str] = mapped_column(String(1), nullable=True)
    certifier_last_name: Mapped[str] = mapped_column(String(20), nullable=True)
    certifier_suffix: Mapped[str] = mapped_column(String(3), nullable=True)
    certifier_title: Mapped[str] = mapped_column(String(40), nullable=True)
    gender: Mapped[str] = mapped_column(String(1), nullable=True)
    african_american: Mapped[str] = mapped_column(String(1), nullable=True)
    native_american: Mapped[str] = mapped_column(String(1), nullable=True)
    hawaiian: Mapped[str] = mapped_column(String(1), nullable=True)
    asian: Mapped[str] = mapped_column(String(1), nullable=True)
    white: Mapped[str] = mapped_column(String(1), nullable=True)
    ethnicity: Mapped[str] = mapped_column(String(1), nullable=True)
    effective_date: Mapped[str] = mapped_column(String(10), nullable=True)
    last_action_date: Mapped[str] = mapped_column(String(10), nullable=True)
    auction_id: Mapped[int] = mapped_column(Integer)
    reg_stat_broad_serv: Mapped[str] = mapped_column(String(1), nullable=True)
    band_manager: Mapped[str] = mapped_column(String(1), nullable=True)
    type_serv_broad_serv: Mapped[str] = mapped_column(String(1), nullable=True)
    alien_ruling: Mapped[str] = mapped_column(String(1), nullable=True)
    licensee_name_change: Mapped[str] = mapped_column(String(1), nullable=True)
    whitespace_ind: Mapped[str] = mapped_column(String(1), nullable=True)
    additional_cert_choice: Mapped[str] = mapped_column(String(1), nullable=True)
    additional_cert_answer: Mapped[str] = mapped_column(String(1), nullable=True)
    discontinuation_ind: Mapped[str] = mapped_column(String(1), nullable=True)
    regulatory_compliance_ind: Mapped[str] = mapped_column(String(1), nullable=True)
    eligibility_cert_900: Mapped[str] = mapped_column(String(1), nullable=True)
    transition_plan_cert_900: Mapped[str] = mapped_column(String(1), nullable=True)
    return_spectrum_cert_900: Mapped[str] = mapped_column(String(1), nullable=True)
    payment_cert_900: Mapped[str] = mapped_column(String(1), nullable=True)

    @validates("grant_date")
    def validate_grant_date(
        self, name: str, value: str | datetime.date
    ) -> datetime.date | None:
        return validate_date_field(name, value)

    @validates("expired_date")
    def validate_expired_date(
        self, name: str, value: str | datetime.date
    ) -> datetime.date | None:
        return validate_date_field(name, value)

    @validates("cancellation_date")
    def validate_cancellation_date(
        self, name: str, value: str | datetime.date
    ) -> datetime.date | None:
        return validate_date_field(name, value)


class Comment(Base):
    __tablename__: str = "comment"

    record_type: Mapped[str] = mapped_column(String(2), nullable=False)
    unique_system_identifier: Mapped[int] = mapped_column(
        ForeignKey("entity.unique_system_identifier"),
    )
    uls_file_number: Mapped[str] = mapped_column(String(14), nullable=True)
    call_sign: Mapped[str] = mapped_column(String(10), nullable=True)
    comment_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    status_code: Mapped[str] = mapped_column(String(1), nullable=True)
    status_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    _id: Mapped[int] = mapped_column(Integer, primary_key=True)

    @validates("comment_date")
    def validate_comment_date(
        self, name: str, value: str | datetime.date
    ) -> datetime.date | None:
        return validate_date_field(name, value)

    @validates("status_date")
    def validate_status_date(
        self, name: str, value: str | datetime.date
    ) -> datetime.date | None:
        return validate_date_field(name, value)


class LicenseAttachment(Base):
    __tablename__: str = "license_attachment"

    record_type: Mapped[str] = mapped_column(String(2), nullable=False)
    unique_system_identifier: Mapped[int] = mapped_column(
        ForeignKey("entity.unique_system_identifier"),
    )
    call_sign: Mapped[str] = mapped_column(String(10), nullable=True)
    attachment_code: Mapped[str] = mapped_column(String(1), nullable=True)
    attachment_desc: Mapped[str] = mapped_column(String(60), nullable=True)
    attachment_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    attachment_filename: Mapped[str] = mapped_column(String(60), nullable=True)
    action_performed: Mapped[str] = mapped_column(String(1), nullable=True)
    _id: Mapped[int] = mapped_column(Integer, primary_key=True)

    @validates("attachment_date")
    def validate_attachment_date(
        self, name: str, value: str | datetime.date
    ) -> datetime.date | None:
        return validate_date_field(name, value)


class LicenseFreeformSpecialCondition(Base):
    __tablename__: str = "license_freeform_special_condition"

    record_type: Mapped[str] = mapped_column(String(2), nullable=False)
    unique_system_identifier: Mapped[int] = mapped_column(
        ForeignKey("entity.unique_system_identifier"),
    )
    uls_file_number: Mapped[str] = mapped_column(String(14), nullable=True)
    ebf_number: Mapped[str] = mapped_column(String(30), nullable=True)
    call_sign: Mapped[str] = mapped_column(String(10), nullable=True)
    lic_freeform_cond_type: Mapped[str] = mapped_column(String(1), nullable=True)
    unique_lic_freeform_id: Mapped[int] = mapped_column(Integer, nullable=True)
    sequence_number: Mapped[int] = mapped_column(Integer)
    lic_freeform_condition: Mapped[str] = mapped_column(String(255), nullable=True)
    status_code: Mapped[str] = mapped_column(String(1), nullable=True)
    status_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    _id: Mapped[int] = mapped_column(Integer, primary_key=True)

    @validates("status_date")
    def validate_status_date(
        self, name: str, value: str | datetime.date
    ) -> datetime.date | None:
        return validate_date_field(name, value)


class LicenseSpecialCondition(Base):
    __tablename__: str = "license_special_condition"

    record_type: Mapped[str] = mapped_column(String(2), nullable=False)
    unique_system_identifier: Mapped[int] = mapped_column(
        ForeignKey("entity.unique_system_identifier"),
    )
    uls_file_number: Mapped[str] = mapped_column(String(14), nullable=True)
    ebf_number: Mapped[str] = mapped_column(String(30), nullable=True)
    call_sign: Mapped[str] = mapped_column(String(10), nullable=True)
    special_condition_type: Mapped[str] = mapped_column(String(1), nullable=True)
    special_condition_code: Mapped[int] = mapped_column(Integer)
    status_code: Mapped[str] = mapped_column(String(1), nullable=True)
    status_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    _id: Mapped[int] = mapped_column(Integer, primary_key=True)

    @validates("status_date")
    def validate_status_date(
        self, name: str, value: str | datetime.date
    ) -> datetime.date | None:
        return validate_date_field(name, value)


if __name__ == "__main__":
    engine = create_engine("sqlite:///license.db", echo=True)
    Base.metadata.create_all(engine)
    session = Session(engine)
