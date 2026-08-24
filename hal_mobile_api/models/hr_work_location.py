<?xml version="1.0" encoding="UTF-8"?>
<odoo>

    <record id="view_hr_work_location_form_hal_mobile" model="ir.ui.view">
        <field name="name">hr.work.location.form.hal.mobile</field>
        <field name="model">hr.work.location</field>

        <field name="inherit_id" ref="hr.hr_work_location_view_form"/>

        <field name="arch" type="xml">

            <xpath expr="//field[@name='address_id']" position="after">

                <field name="hal_latitude"/>

                <field name="hal_longitude"/>

                <field name="hal_attendance_radius"/>

            </xpath>

        </field>
    </record>

</odoo>
