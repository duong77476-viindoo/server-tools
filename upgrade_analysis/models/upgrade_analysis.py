# Copyright 2011-2015 Therp BV <https://therp.nl>
# Copyright 2016-2020 Opener B.V. <https://opener.am>
# Copyright 2019 ForgeFlow <https://forgeflow.com>
# Copyright 2020 GRAP <https://grap.coop>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# flake8: noqa: C901

import logging
import os
from copy import deepcopy

from lxml import etree
from mako.template import Template

from odoo import fields, models, release
from odoo.exceptions import ValidationError
from odoo.modules import get_module_path
from odoo.tools import config
from odoo.tools.convert import nodeattr2bool
from odoo.tools.translate import _

try:
    from odoo.addons.openupgrade_scripts.apriori import merged_modules, renamed_modules
except ImportError:
    renamed_modules = {}
    merged_modules = {}

from .. import compare

_logger = logging.getLogger(__name__)
_IGNORE_MODULES = ["openupgrade_records", "upgrade_analysis"]
_TVTMAADDONS16 = ["l10n_vn_edi_summary","l10n_vn_viin","l10n_vn_viin_account_auto_transfer","l10n_vn_viin_account_balance_carry_forward","l10n_vn_viin_account_qr_code_emv","l10n_vn_viin_accounting_sinvoice","l10n_vn_viin_accounting_sinvoice_patch1","l10n_vn_viin_accounting_vninvoice","l10n_vn_viin_accounting_vninvoice_summary","l10n_vn_viin_edi","l10n_vn_viin_edi_patch1","l10n_vn_viin_einvoice_sale","l10n_vn_viin_foreign_trade","l10n_vn_viin_hr_account","l10n_vn_viin_hr_payroll","l10n_vn_viin_hr_payroll_account","l10n_vn_viin_hr_payroll_account_overtime","l10n_vn_viin_hr_payroll_administrative_region","l10n_vn_viin_hr_payroll_meal_account","l10n_vn_viin_loan_management","l10n_vn_viin_picking_operation","l10n_vn_viin_stock_reports","l10n_vn_viin_stock_reports_multi_warehouse_access_control","l10n_vn_viin_vat_counterpart","payment_momo_viin","payment_nganluong","payment_vnpay","payment_zalopay","test_pylint","test_stock_dropshipping","test_to_signup_email_verification","test_viin_mail_route","test_viin_user_assignment_log_project","to_account_balance_carry_forward","to_account_counterpart","to_account_payment","to_accounting_bi","to_accounting_entry_report_flag","to_approvals","to_attendance_device","to_backdate","to_bank_currency_rate","to_bank_currency_rate_purchase_stock","to_base","to_common_uom","to_company_hotline","to_config_management","to_currency_conversion_diff","to_employee_changes_tracking","to_employee_documents","to_enterprice_marks_inter_company","to_enterprise_mobile","to_equipment_maintenance_schedule","to_equipment_woking_frequency","to_erponline_utility","to_event_project","to_event_timesheet","to_fee_definition","to_fee_definition_sale","to_fleet_accounting","to_fleet_accounting_fleet_operation","to_fleet_accounting_fleet_operation_revenue","to_fleet_driver","to_fleet_driver_job_wage","to_fleet_insurance_basic","to_fleet_load_params","to_fleet_operation_planning","to_fleet_specs","to_fleet_stock","to_fleet_stock_account","to_fleet_stock_picking","to_fleet_vehicle_revenue","to_fleet_vehicle_revenue_accounting","to_geo_routes","to_git","to_git_odoo_version","to_git_project","to_hide_ent_modules_website_theme_install","to_hr_barcode_in_emp_name","to_hr_employee_advance","to_hr_employee_grade","to_hr_employee_relative","to_hr_employee_resign","to_hr_expense","to_hr_expense_employee_advance","to_hr_expense_payroll","to_hr_meal","to_hr_payroll","to_hr_payroll_account","to_hr_payroll_attendance","to_hr_payroll_meal","to_hr_project_timesheet_timeoff_payroll","to_hr_shift_rotation","to_hr_timesheet_approval","to_hr_timesheet_payroll","to_hr_training","to_invoice_line_summary","to_invoice_tax_details","to_legal_invoice_number","to_loan_management","to_location_warehouse","to_mail_notif_and_email","to_mail_template_multilang_fix","to_maintenance_approval","to_maintenance_by_working_hours","to_maintenance_notification","to_maintenance_request_simple_mediate","to_mrp_backdate","to_mrp_bom_component_percentage","to_mrp_bom_stock_value","to_multi_warehouse_access_control","to_multi_warehouse_access_control_mrp","to_multi_warehouse_access_control_purchase","to_multi_warehouse_access_control_sale","to_multi_warehouse_access_control_sms","to_odoo_module","to_odoo_module_sale","to_odoo_module_sale_project","to_odoo_module_sale_template","to_odoo_version","to_okr","to_okr_project","to_org_chart","to_partner_dob","to_partner_dob_send_email","to_partner_equity_range","to_partner_multilang","to_partner_multilang_partner_autocomplete","to_partner_nationality","to_partner_tax_code","to_partner_track_change","to_payment_transaction_protection","to_paypal_unsupported_currencies","to_payroll_payment_acb_templates","to_pos_analytics","to_pos_delivery","to_pos_note","to_pos_order_to_sales_order","to_procurement_approval","to_product_code_sequence","to_product_collection","to_product_collection_pos","to_product_collection_sale","to_product_dimensions","to_product_function","to_product_function_pos","to_product_function_sale","to_product_license","to_product_license_sale","to_product_maintenance_schedule","to_product_milestone","to_product_odoo_version","to_product_return_reason","to_product_return_reason_stock","to_product_standard_price_access","to_product_standard_price_access_account","to_product_standard_price_access_purchase","to_promotion_voucher","to_promotion_voucher_account_payment","to_promotion_voucher_l10n_vn","to_promotion_voucher_pos","to_promotion_voucher_pos_return","to_promotion_voucher_pos_sale","to_promotion_voucher_sale","to_purchase_backdate","to_purchase_bom_stock_value","to_purchase_landed_cost","to_purchase_line_numbering","to_purchase_order_advance","to_purchase_receipt","to_refund_account","to_registration_email_blacklist","to_repair_request_from_maintenance","to_repair_timesheet","to_repair_with_maintenance_schedule","to_safe_confirm_button","to_sale_backdate","to_sale_desc_short_link","to_sale_line_numbering","to_sale_loyalty_patch_1","to_sale_order_advance","to_sale_price_lock","to_sale_subscription","to_sales_stock_schedule","to_sales_target","to_sales_target_pos","to_sales_target_sale","to_sales_team_advanced","to_sales_team_advanced_crm","to_sales_team_advanced_sale","to_signup_email_verification","to_sshkey","to_stock_account_moves_link","to_stock_age_report","to_stock_block_quantity","to_stock_equipment","to_stock_equipment_bom_kit","to_stock_equipment_hierarchy","to_stock_product_allocation_approval","to_stock_report_common","to_token_expiration","to_token_expiration_test","to_unique_product_code","to_uom_subscription","to_upload_file","to_vat_counterpart","to_vendor_price_lock","to_vietnam_bank_icons","to_vietnamese_number2words","to_wallet","to_wallet_adjustment","to_wallet_currency_conversion_diff","to_wallet_sale","to_warranty_management","to_warranty_purchase","to_warranty_purchase_stock","to_warranty_sale","to_warranty_sale_stock","to_warranty_stock","to_web_thousand_sep","to_website_apps_store","to_website_base","to_website_docs","to_website_docs_odoo","to_website_docs_odoo_data","to_website_odoo_version","to_website_recaptcha","to_website_recaptcha_signup","to_website_slides_event","viin_account","viin_account_approval","viin_account_auto_transfer","viin_account_auto_transfer_patch_1","viin_account_bank_statement_import","viin_account_bank_statement_import_rje","viin_account_counterpart_reconciliation","viin_account_onbehalf_payment","viin_account_onbehalf_payment_currency_conversion_diff","viin_account_qr_code_emv","viin_account_reconciliation","viin_administrative_region","viin_affiliate","viin_affiliate_crm","viin_affiliate_loyalty","viin_affiliate_loyalty_pos","viin_affiliate_loyalty_sale","viin_affiliate_marketplace_sale","viin_affiliate_multi_level","viin_affiliate_multi_level_pos","viin_affiliate_multi_level_sale","viin_affiliate_pos","viin_affiliate_pos_discount","viin_affiliate_pos_sale","viin_affiliate_sale","viin_affiliate_sale_crm","viin_affiliate_website","viin_affiliate_website_crm_livechat","viin_affiliate_website_patch","viin_affiliate_website_project","viin_affilitate_purchase","viin_analytic","viin_analytic_account","viin_analytic_hr_expense","viin_analytic_purchase","viin_analytic_sale","viin_analytic_stock","viin_analytic_tag","viin_analytic_tag_expense","viin_analytic_tag_purchase","viin_analytic_tag_purchase_requisition","viin_analytic_tag_purchase_stock","viin_analytic_tag_sale","viin_analytic_tag_sale_project","viin_base_district","viin_base_import_tracking","viin_base_state_group","viin_built_in_help","viin_coach_approvals","viin_contacts_district","viin_country_target_market","viin_crm_business_nature","viin_crm_customer_recognition","viin_crm_dob","viin_equipment_warranty_partner_infor","viin_event_barcodes","viin_event_checkin","viin_event_checkin_crm","viin_event_partner_barcodes","viin_fee_definition_sale_project","viin_fleet","viin_fleet_accounting_purchase","viin_fleet_vehicle_revenue_accounting_sale","viin_foreign_trade","viin_foreign_trade_currency_rate","viin_geography_info","viin_geography_info_contact","viin_geography_info_world_bank","viin_google_drive","viin_google_spreadsheet","viin_helpdesk","viin_helpdesk_crm","viin_helpdesk_hr","viin_helpdesk_livechat","viin_helpdesk_odoo_module","viin_helpdesk_odoo_version","viin_helpdesk_sale","viin_helpdesk_severity","viin_helpdesk_team_ticket_type","viin_helpdesk_ticket_properties","viin_helpdesk_timesheet","viin_hr","viin_hr_account","viin_hr_assignment_log","viin_hr_attendance_validation","viin_hr_contract","viin_hr_employee_birthday","viin_hr_employee_relative_birthdate","viin_hr_holidays","viin_hr_maintenance","viin_hr_overtime","viin_hr_overtime_approval","viin_hr_overtime_approval_payroll","viin_hr_overtime_attendance","viin_hr_overtime_payroll","viin_hr_overtime_timeoff","viin_hr_overtime_timesheet","viin_hr_overtime_timesheet_approval","viin_hr_overtime_timesheet_attendance","viin_hr_payroll_administrative_region","viin_hr_payroll_timesheet_wfh","viin_hr_project","viin_hr_rank","viin_hr_recruitment","viin_hr_recruitment_approval","viin_hr_recruitment_skills_resume","viin_hr_role","viin_hr_seniority","viin_hr_skill_framework","viin_hr_skill_framework_recruitment","viin_hr_timesheet_timer","viin_hr_work_entry","viin_hr_work_entry_contract","viin_hr_work_entry_contract_attendance","viin_hr_work_entry_contract_attendance_holiday","viin_hr_work_entry_holidays","viin_inventory_adjustment_with_cost_price","viin_l10n_vn_accounting_vninvoice_summary","viin_link_tracker_qr_code","viin_loyalty","viin_loyalty_pos","viin_loyalty_pos_sale","viin_loyalty_sale","viin_mail_channel_privacy","viin_mail_mention_with_avatar","viin_mail_route","viin_mail_search","viin_mail_show_recipient","viin_mail_thread_account","viin_mail_thread_product","viin_mail_thread_purchase","viin_mail_thread_stock","viin_mail_thread_stock_account","viin_mail_thread_uom","viin_mail_tracking","viin_maintenance","viin_maintenance_preventive_mode","viin_marketplace","viin_marketplace_approval","viin_marketplace_event_sale","viin_marketplace_loyalty","viin_marketplace_partner_approval","viin_marketplace_product_approval","viin_marketplace_rating","viin_marketplace_sale","viin_marketplace_sale_currency_conversion_diff","viin_marketplace_sale_loyalty","viin_marketplace_sale_product_configurator","viin_marketplace_sale_purchase","viin_marketplace_sale_stock","viin_marketplace_snailmail","viin_marketplace_stock","viin_marketplace_website_partner_approval","viin_marketplace_website_sale","viin_marketplace_website_sale_approval","viin_marketplace_website_sale_stock","viin_meeting_room","viin_message_edit_lock","viin_multi_warehouse_access_control_purchase_requisition","viin_partner_access","viin_partner_access_account","viin_partner_access_purchase","viin_partner_access_sale","viin_partner_approval","viin_partner_business_nature","viin_partner_country_recognition","viin_partner_filter","viin_partner_gender","viin_partner_shareholder","viin_partner_tax_code","viin_pdf_print_preview","viin_pos_account_qr_code_emv","viin_pos_custom_bill_logo","viin_pos_refund","viin_pos_return","viin_pos_scale","viin_pos_vnpay","viin_pricelist_validity_advance","viin_product_approval","viin_project","viin_project_access_timesheet","viin_project_progress","viin_project_timesheet_leave","viin_purchase","viin_purchase_approval","viin_purchase_stock_backdate","viin_queue","viin_repair","viin_repair_access_group","viin_repair_discount","viin_repair_request_from_warranty","viin_repair_supply","viin_resource","viin_resource_calendar_rate","viin_sale_approval","viin_sale_crm_follower_access_right","viin_sale_product_duplication_warning","viin_sale_project","viin_sale_project_technician","viin_sale_quotation_template_access","viin_sales_team_collaboration","viin_sales_team_collaboration_crm","viin_sales_team_collaboration_sale","viin_sales_unlink","viin_sales_unlink_stock","viin_social","viin_social_facebook","viin_social_facebook_verify","viin_social_lead","viin_social_linkedin","viin_spreadsheet_dashboard","viin_stock_account_backdate","viin_stock_approval","viin_stock_backdate","viin_stock_internal_transit_valuation","viin_stock_internal_transit_valuation_specific_identification","viin_stock_landed_costs","viin_stock_lot_dropshipping_partner_infor","viin_stock_lot_partner_infor","viin_stock_specific_identification","viin_stock_specific_identification_landed_costs","viin_stock_specific_identification_purchase_stock","viin_survey_exam","viin_survey_recompute_results","viin_transfer_address","viin_unicode_slugify","viin_user_assignment_log","viin_wallet_affiliate","viin_wallet_loyalty","viin_wallet_marketplace_sale","viin_wallet_patch1","viin_wallet_sale_loyalty","viin_web_countup_timer","viin_web_editor","viin_website","viin_website_blog_access_right","viin_website_blog_toc","viin_website_event_checkin","viin_website_form_helpdesk","viin_website_forum_security_groups","viin_website_gtm","viin_website_helpdesk","viin_website_helpdesk_ticket_properties","viin_website_hr_recruitment_website_editor","viin_website_livechat","viin_website_multilingual_multimedia","viin_website_nofollow","viin_website_page_access_right","viin_website_partner_approval","viin_website_partner_business_nature","viin_website_sale_approval"]
_ERP16 = ["l10n_vn_viin_account_asset","l10n_vn_viin_account_reports","l10n_vn_viin_mrp_subcontracting_account","l10n_vn_viin_mrp_subcontracting_settlement","to_account_accountant","to_account_asset","to_account_asset_purchase","to_account_budget","to_account_budget_hr_timesheet","to_account_budget_patch1","to_account_reports","to_account_reports_report_off","to_hide_ent_modules","to_hide_ent_modules_payment","to_hide_ent_modules_website_theme","to_inter_company_base","to_inter_company_invoice","to_inter_company_sale_purchase","to_inter_company_sale_purchase_stock","to_mrp_account_standard_consumption","to_mrp_barcode","to_mrp_maintenance","to_mrp_mps","to_mrp_multi_warehouse_access_control","to_mrp_plm","to_mrp_workorder","to_quality","to_quality_mrp","to_quality_stock","to_stock_asset","to_stock_asset_equipment","to_stock_barcode","viin_account_budget_project","viin_account_followup","viin_account_followup_sale","viin_account_subscription","viin_amazon","viin_amazon_ses","viin_analytic_tag_asset","viin_appointment","viin_appointment_crm","viin_appointment_sale","viin_appointment_sale_crm","viin_appointment_website","viin_appointment_website_hr","viin_auto_currency_rate","viin_auto_currency_rate_acb","viin_auto_currency_rate_vcb","viin_auto_currency_rate_xe","viin_contacts_map","viin_crm","viin_crm_sankey","viin_customizer","viin_customizer_web_responsive","viin_document","viin_document_account","viin_document_hr","viin_document_hr_contract","viin_document_hr_payroll","viin_document_hr_recruitment","viin_document_mrp","viin_document_project","viin_document_purchase","viin_document_sale","viin_document_stock","viin_employee_map","viin_features_activate_account","viin_features_activate_approvals","viin_features_activate_contacts","viin_features_activate_hr","viin_features_activate_hr_attendance","viin_features_activate_hr_expense","viin_features_activate_hr_payroll","viin_features_activate_hr_recruitment","viin_features_activate_inter_company","viin_features_activate_mrp","viin_features_activate_pos","viin_features_activate_product","viin_features_activate_project","viin_features_activate_purchase","viin_features_activate_quality","viin_features_activate_sale","viin_features_activate_stock","viin_features_activate_survey","viin_features_activate_website","viin_fleet_operation_planning_gantt","viin_google_translate_api","viin_iot","viin_iot_pos","viin_iot_pos_restaurant","viin_lang_detection","viin_mail_ice_server_data","viin_mobile","viin_mobile_messenger","viin_mrp","viin_mrp_account","viin_mrp_barcode_backdate","viin_mrp_filter","viin_mrp_landed_costs","viin_mrp_plm_approval","viin_mrp_plm_subcontracting_purchase","viin_mrp_plm_test_full","viin_mrp_product_packaging","viin_mrp_production_progress","viin_mrp_progress","viin_mrp_standard_consumption","viin_mrp_subcontracting_link","viin_mrp_subcontracting_loss_report","viin_mrp_subcontracting_report","viin_mrp_subcontracting_request","viin_mrp_subcontracting_request_approval","viin_mrp_subcontracting_request_plm","viin_mrp_subcontracting_request_requisition","viin_product_recurring","viin_project_gantt","viin_project_scrum","viin_project_scrum_gantt","viin_project_scrum_helpdesk","viin_quality_stock_access_control","viin_rental","viin_rental_stock","viin_sale","viin_sale_crm","viin_sale_mrp_production_progress","viin_sale_recurring","viin_sale_sankey","viin_sale_subscription","viin_sale_subscription_loyalty","viin_sem","viin_sem_crawler","viin_sem_crawler_helpdesk","viin_sem_heatmap","viin_sem_helpdesk","viin_sem_helpdesk_timesheet","viin_sem_project","viin_sem_website_blog","viin_sem_website_forum","viin_stock","viin_stock_patch1","viin_subscription","viin_web_cohort","viin_web_gantt","viin_web_map","viin_web_sankey","viin_website_auto_translation","viin_website_auto_translation_blog","viin_website_auto_translation_google","viin_website_sale_subscription","viin_website_seo","viin_website_seo_advisor","viin_website_seo_advisor_blog","viin_website_seo_blog","viin_website_seo_event","viin_website_seo_forum","viin_website_seo_hr_recruitment","viin_website_seo_sale","viin_website_seo_sale_stock","viin_website_seo_slides"]
_BRANDING16 = ["to_backend_theme","viin_brand","viin_brand_account","viin_brand_auth_oauth","viin_brand_auth_totp","viin_brand_auth_totp_mail_enforce","viin_brand_auth_totp_portal","viin_brand_base_import","viin_brand_base_setup","viin_brand_calendar","viin_brand_common","viin_brand_contacts","viin_brand_crm","viin_brand_digest","viin_brand_fleet","viin_brand_hr","viin_brand_hr_expense","viin_brand_hr_recruitment","viin_brand_hr_skills","viin_brand_iap","viin_brand_im_livechat","viin_brand_mail","viin_brand_mail_bot","viin_brand_mail_plugin","viin_brand_mass_mailing","viin_brand_mass_mailing_crm","viin_brand_mass_mailing_sale","viin_brand_mass_mailing_sms","viin_brand_mass_mailing_themes","viin_brand_membership","viin_brand_mrp","viin_brand_note","viin_brand_payment","viin_brand_payment_authorize","viin_brand_payment_paypal","viin_brand_portal","viin_brand_pos","viin_brand_pos_mercury","viin_brand_product","viin_brand_purchase","viin_brand_purchase_stock","viin_brand_sale","viin_brand_sale_management","viin_brand_sale_quotation_builder","viin_brand_sale_stock","viin_brand_snailmail","viin_brand_social_media","viin_brand_stock","viin_brand_stock_account","viin_brand_web_unsplash","viin_brand_website","viin_brand_website_event","viin_brand_website_event_exhibitor","viin_brand_website_forum","viin_brand_website_links","viin_brand_website_livechat","viin_brand_website_profile","viin_brand_website_sale","viin_brand_website_slides","web_chatter_position","web_responsive"]

class UpgradeAnalysis(models.Model):
    _name = "upgrade.analysis"
    _description = "Upgrade Analyses"

    analysis_date = fields.Datetime(readonly=True)

    state = fields.Selection(
        [("draft", "draft"), ("done", "Done")], readonly=True, default="draft"
    )
    config_id = fields.Many2one(
        string="Comparison Config",
        comodel_name="upgrade.comparison.config",
        readonly=True,
        required=True,
    )

    log = fields.Text(readonly=True)
    upgrade_path = fields.Char(
        compute="_compute_upgrade_path",
        store=True,
        readonly=False,
        help=(
            "The base file path to save the analyse files of Odoo modules. "
            "Taken from Odoo's --upgrade-path command line option or the "
            "'scripts' subdirectory in the openupgrade_scripts addon."
        ),
    )
    write_files = fields.Boolean(
        help="Write analysis files to the module directories", default=True
    )

    def _compute_upgrade_path(self):
        """Return the --upgrade-path configuration option or the `scripts`
        directory in `openupgrade_scripts` if available
        """
        res = config.get("upgrade_path", False)
        if not res:
            module_path = get_module_path("openupgrade_scripts", display_warning=False)
            if module_path:
                res = os.path.join(module_path, "scripts")
        self.upgrade_path = res

    def _get_remote_model(self, connection, model):
        self.ensure_one()
        if model == "record":
            if float(self.config_id.version) < 14.0:
                return connection.env["openupgrade.record"]
            else:
                return connection.env["upgrade.record"]
        return False

    def _write_file(
        self, module_name, version, content, filename="upgrade_analysis.txt"
    ):
        module = self.env["ir.module.module"].search([("name", "=", module_name)])[0]
        if module.is_odoo_module:
            return
            if not self.upgrade_path:
                return (
                    "ERROR: no upgrade_path set when writing analysis of %s\n"
                    % module_name
                )
            full_path = os.path.join(self.upgrade_path, module_name, version)
        elif module_name in _TVTMAADDONS16 or module_name in _ERP16 or module_name in _BRANDING16:
            if module_name in _TVTMAADDONS16:
                full_path = os.path.join("/home/duongnguyen/git/odoo-openupgrade-tvtmaaddons/odoo-openupgrade-tvtmaaddons16", module_name, version)
            elif module_name in _ERP16:
                full_path = os.path.join("/home/duongnguyen/git/odoo-openupgrade-erp/odoo-openupgrade-erp16", module_name, version)
            elif module_name in _BRANDING16:
                full_path = os.path.join("/home/duongnguyen/git/odoo-openupgrade-branding/odoo-openupgrade-branding16", module_name, version)
        else:
            full_path = os.path.join(
                get_module_path(module_name), "migrations", version
            )
            return
        if not os.path.exists(full_path):
            try:
                os.makedirs(full_path)
            except os.error:
                return "ERROR: could not create migrations directory %s:\n" % (
                    full_path
                )
        logfile = os.path.join(full_path, filename)
        try:
            f = open(logfile, "w")
        except Exception:
            return "ERROR: could not open file %s for writing:\n" % logfile
        _logger.debug("Writing analysis to %s", logfile)
        f.write(content)
        f.close()
        return None

    def analyze(self):
        """
        Retrieve both sets of database representations,
        perform the comparison and register the resulting
        change set
        """
        self.ensure_one()
        self.write(
            {
                "analysis_date": fields.Datetime.now(),
            }
        )

        connection = self.config_id.get_connection()
        RemoteRecord = self._get_remote_model(connection, "record")
        LocalRecord = self.env["upgrade.record"]

        # Retrieve field representations and compare
        remote_records = RemoteRecord.field_dump()
        local_records = LocalRecord.field_dump()
        res = compare.compare_sets(remote_records, local_records)

        # Retrieve xml id representations and compare
        flds = [
            "module",
            "model",
            "name",
            "noupdate",
            "prefix",
            "suffix",
            "domain",
            "definition",
        ]
        local_xml_records = [
            {field: record[field] for field in flds}
            for record in LocalRecord.search([("type", "=", "xmlid")])
        ]
        remote_xml_record_ids = RemoteRecord.search([("type", "=", "xmlid")])
        remote_xml_records = [
            {field: record[field] for field in flds}
            for record in RemoteRecord.read(remote_xml_record_ids, flds)
        ]
        res_xml = compare.compare_xml_sets(remote_xml_records, local_xml_records)

        # Retrieve model representations and compare
        flds = [
            "module",
            "model",
            "name",
            "model_original_module",
            "model_type",
        ]
        local_model_records = [
            {field: record[field] for field in flds}
            for record in LocalRecord.search([("type", "=", "model")])
        ]
        remote_model_record_ids = RemoteRecord.search([("type", "=", "model")])
        remote_model_records = [
            {field: record[field] for field in flds}
            for record in RemoteRecord.read(remote_model_record_ids, flds)
        ]
        res_model = compare.compare_model_sets(
            remote_model_records, local_model_records
        )

        affected_modules = sorted(
            {
                record["module"]
                for record in remote_records
                + local_records
                + remote_xml_records
                + local_xml_records
                + remote_model_records
                + local_model_records
            }
        )
        if "base" in affected_modules:
            try:
                pass
            except ImportError:
                _logger.error(
                    "You are using upgrade_analysis on core modules without "
                    " having openupgrade_scripts module available."
                    " The analysis process will not work properly,"
                    " if you are generating analysis for the odoo modules"
                    " in an openupgrade context."
                )

        # reorder and output the result
        keys = ["general"] + affected_modules
        modules = {
            module["name"]: module
            for module in self.env["ir.module.module"].search(
                [("state", "=", "installed")]
            )
        }
        general_log = ""

        no_changes_modules = []

        for ignore_module in _IGNORE_MODULES:
            if ignore_module in keys:
                keys.remove(ignore_module)

        for key in keys:
            contents = "---Models in module '%s'---\n" % key
            if key in res_model:
                contents += "\n".join([str(line) for line in res_model[key]])
                if res_model[key]:
                    contents += "\n"
            contents += "---Fields in module '%s'---\n" % key
            if key in res:
                contents += "\n".join([str(line) for line in sorted(res[key])])
                if res[key]:
                    contents += "\n"
            contents += "---XML records in module '%s'---\n" % key
            if key in res_xml:
                contents += "\n".join([str(line) for line in res_xml[key]])
                if res_xml[key]:
                    contents += "\n"
            if key not in res and key not in res_xml and key not in res_model:
                contents += "---nothing has changed in this module--\n"
                no_changes_modules.append(key)
            if key == "general":
                general_log += contents
                continue
            if compare.module_map(key) not in modules:
                general_log += (
                    "ERROR: module not in list of installed modules:\n" + contents
                )
                continue
            if key not in modules:
                # no need to log in full log the merged/renamed modules
                continue
            if self.write_files:
                error = self._write_file(key, modules[key].installed_version, contents)
                if error:
                    general_log += error
                    general_log += contents
            else:
                general_log += contents

        # Store the full log
        if self.write_files and "base" in modules:
            self._write_file(
                "base",
                modules["base"].installed_version,
                general_log,
                "upgrade_general_log.txt",
            )

        try:
            self.generate_noupdate_changes()
        except Exception as e:
            _logger.exception("Error generating noupdate changes: %s" % e)
            general_log += "ERROR: error when generating noupdate changes: %s\n" % e

        try:
            self.generate_module_coverage_file(no_changes_modules)
        except Exception as e:
            _logger.exception("Error generating module coverage file: %s" % e)
            general_log += "ERROR: error when generating module coverage file: %s\n" % e

        self.write(
            {
                "state": "done",
                "log": general_log,
            }
        )
        return True

    @staticmethod
    def _get_node_dict(element):
        res = {}
        if element is None:
            return res
        for child in element:
            if "name" in child.attrib:
                key = "./{}[@name='{}']".format(child.tag, child.attrib["name"])
                res[key] = child
        return res

    @staticmethod
    def _get_node_value(element):
        if "eval" in element.attrib.keys():
            return element.attrib["eval"]
        if "ref" in element.attrib.keys():
            return element.attrib["ref"]
        if not len(element):
            return element.text
        return etree.tostring(element)

    def _get_xml_diff(
        self, remote_update, remote_noupdate, local_update, local_noupdate
    ):
        odoo = etree.Element("odoo")
        for xml_id in sorted(local_noupdate.keys()):
            local_record = local_noupdate[xml_id]
            remote_record = None
            if xml_id in remote_update and xml_id not in remote_noupdate:
                remote_record = remote_update[xml_id]
            elif xml_id in remote_noupdate:
                remote_record = remote_noupdate[xml_id]

            if "." in xml_id:
                module_xmlid = xml_id.split(".", 1)[0]
            else:
                module_xmlid = ""

            if remote_record is None and not module_xmlid:
                continue

            if local_record.tag == "template":
                old_tmpl = etree.tostring(remote_record, encoding="utf-8")
                new_tmpl = etree.tostring(local_record, encoding="utf-8")
                if old_tmpl != new_tmpl:
                    odoo.append(local_record)
                continue

            element = etree.Element(
                "record", id=xml_id, model=local_record.attrib["model"]
            )
            # Add forcecreate attribute if exists
            if local_record.attrib.get("forcecreate"):
                element.attrib["forcecreate"] = local_record.attrib["forcecreate"]
            record_remote_dict = self._get_node_dict(remote_record)
            record_local_dict = self._get_node_dict(local_record)
            for key in sorted(record_remote_dict.keys()):
                if not local_record.xpath(key):
                    # The element is no longer present.
                    # Does the field still exist?
                    if record_remote_dict[key].tag == "field":
                        field_name = remote_record.xpath(key)[0].attrib.get("name")
                        if (
                            field_name
                            not in self.env[local_record.attrib["model"]]._fields.keys()
                        ):
                            continue
                    # Overwrite an existing value with an empty one.
                    attribs = deepcopy(record_remote_dict[key]).attrib
                    for attr in ["eval", "ref"]:
                        if attr in attribs:
                            del attribs[attr]
                    element.append(etree.Element(record_remote_dict[key].tag, attribs))
                else:
                    oldrepr = self._get_node_value(record_remote_dict[key])
                    newrepr = self._get_node_value(record_local_dict[key])

                    if oldrepr != newrepr:
                        element.append(deepcopy(record_local_dict[key]))

            for key in sorted(record_local_dict.keys()):
                if remote_record is None or not remote_record.xpath(key):
                    element.append(deepcopy(record_local_dict[key]))

            if len(element):
                odoo.append(element)

        if not len(odoo):
            return ""
        return etree.tostring(
            etree.ElementTree(odoo),
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8",
        ).decode("utf-8")

    @staticmethod
    def _update_node(target, source):
        for element in source:
            if "name" in element.attrib:
                query = "./{}[@name='{}']".format(element.tag, element.attrib["name"])
            else:
                # query = "./{}".format(element.tag)
                continue
            for existing in target.xpath(query):
                target.remove(existing)
            target.append(element)

    @classmethod
    def _process_data_node(
        self, data_node, records_update, records_noupdate, module_name
    ):
        noupdate = nodeattr2bool(data_node, "noupdate", False)
        for record in data_node.xpath("./record") + data_node.xpath("./template"):
            self._process_record_node(
                record, noupdate, records_update, records_noupdate, module_name
            )

    @classmethod
    def _process_record_node(
        self, record, noupdate, records_update, records_noupdate, module_name
    ):
        xml_id = record.get("id")
        if not xml_id:
            return
        if "." in xml_id and xml_id.startswith(module_name + "."):
            xml_id = xml_id[len(module_name) + 1 :]
        for records in records_noupdate, records_update:
            # records can occur multiple times in the same module
            # with different noupdate settings
            if xml_id in records:
                # merge records (overwriting an existing element
                # with the same tag). The order processing the
                # various directives from the manifest is
                # important here
                self._update_node(records[xml_id], record)
                break
        else:
            target_dict = records_noupdate if noupdate else records_update
            target_dict[xml_id] = record

    @classmethod
    def _parse_files(self, xml_files, module_name):
        records_update = {}
        records_noupdate = {}
        parser = etree.XMLParser(
            remove_blank_text=True,
            strip_cdata=False,
        )
        for xml_file in xml_files:
            try:
                # This is for a final correct pretty print
                # Ref.: https://stackoverflow.com/a/7904066
                # Also don't strip CDATA tags as needed for HTML content
                root_node = etree.fromstring(xml_file.encode("utf-8"), parser=parser)
            except etree.XMLSyntaxError:
                continue
            # Support xml files with root Element either odoo or openerp
            # Condition: each xml file should have only one root element
            # {<odoo>, <openerp> or —rarely— <data>};
            root_node_noupdate = nodeattr2bool(root_node, "noupdate", False)
            if root_node.tag not in ("openerp", "odoo", "data"):
                raise ValidationError(
                    _("Unexpected root Element: %(root)s in file: %(file)s")
                    % {"root": root_node.getroot(), "file": xml_file}
                )
            for node in root_node:
                if node.tag == "data":
                    self._process_data_node(
                        node, records_update, records_noupdate, module_name
                    )
                elif node.tag == "record":
                    self._process_record_node(
                        node,
                        root_node_noupdate,
                        records_update,
                        records_noupdate,
                        module_name,
                    )

        return records_update, records_noupdate

    def generate_noupdate_changes(self):
        """Communicate with the remote server to fetch all xml data records
        per module, and generate a diff in XML format that can be imported
        from the module's migration script using openupgrade.load_data()
        """
        self.ensure_one()
        connection = self.config_id.get_connection()
        remote_record_obj = self._get_remote_model(connection, "record")
        local_record_obj = self.env["upgrade.record"]
        local_modules = local_record_obj.list_modules()
        all_remote_modules = remote_record_obj.list_modules()
        for local_module in local_modules:
            remote_files = []
            remote_modules = []
            remote_update, remote_noupdate = {}, {}
            for remote_module in all_remote_modules:
                if local_module == renamed_modules.get(
                    remote_module, merged_modules.get(remote_module, remote_module)
                ):
                    remote_files.extend(
                        remote_record_obj.get_xml_records(remote_module)
                    )
                    remote_modules.append(remote_module)
                    add_remote_update, add_remote_noupdate = self._parse_files(
                        remote_files, remote_module
                    )
                    remote_update.update(add_remote_update)
                    remote_noupdate.update(add_remote_noupdate)
            if not remote_modules:
                continue
            local_files = local_record_obj.get_xml_records(local_module)
            local_update, local_noupdate = self._parse_files(local_files, local_module)
            diff = self._get_xml_diff(
                remote_update, remote_noupdate, local_update, local_noupdate
            )
            if diff:
                module = self.env["ir.module.module"].search(
                    [("name", "=", local_module)]
                )
                self._write_file(
                    local_module,
                    module.installed_version,
                    diff,
                    filename="noupdate_changes.xml",
                )
        return True

    def generate_module_coverage_file(self, no_changes_modules):
        self.ensure_one()

        module_coverage_file_folder = config.get("module_coverage_file_folder", False)

        if not module_coverage_file_folder:
            return

        file_template = Template(
            filename=os.path.join(
                get_module_path("upgrade_analysis"),
                "static",
                "src",
                "module_coverage_template.rst.mako",
            )
        )

        module_domain = [
            ("state", "=", "installed"),
            ("name", "not in", ["upgrade_analysis", "openupgrade_records"]),
        ]

        connection = self.config_id.get_connection()
        all_local_modules = (
            self.env["ir.module.module"].search(module_domain).mapped("name")
        )
        all_remote_modules = (
            connection.env["ir.module.module"]
            .browse(connection.env["ir.module.module"].search(module_domain))
            .mapped("name")
        )

        start_version = connection.version
        end_version = release.major_version

        all_modules = sorted(list(set(all_remote_modules + all_local_modules)))
        module_descriptions = {}
        for module in all_modules:
            status = ""
            if module in all_local_modules and module in all_remote_modules:
                module_description = " %s" % module
            elif module in all_local_modules:
                module_description = " |new| %s" % module
            else:
                module_description = " |del| %s" % module

            if module in compare.apriori.merged_modules:
                status = "Merged into %s. " % compare.apriori.merged_modules[module]
            elif module in compare.apriori.renamed_modules:
                status = "Renamed to %s. " % compare.apriori.renamed_modules[module]
            elif module in compare.apriori.renamed_modules.values():
                status = (
                    "Renamed from %s. "
                    % [
                        x
                        for x in compare.apriori.renamed_modules
                        if compare.apriori.renamed_modules[x] == module
                    ][0]
                )
            elif module in no_changes_modules:
                status += "No DB layout changes. "
            module_descriptions[module_description.ljust(49, " ")] = status.ljust(
                49, " "
            )

        rendered_text = file_template.render(
            start_version=start_version,
            end_version=end_version,
            module_descriptions=module_descriptions,
        )

        file_name = "modules{}-{}.rst".format(
            start_version.replace(".", ""),
            end_version.replace(".", ""),
        )

        file_path = os.path.join(module_coverage_file_folder, file_name)
        f = open(file_path, "w+")
        f.write(rendered_text)
        f.close()
        return True
