ALTER TABLE mechanics
ADD COLUMN phone VARCHAR(20) AFTER name,
ADD COLUMN hiring_date DATE AFTER birth_date,
ADD COLUMN address_reference VARCHAR(255) AFTER address_state,
ADD COLUMN emergency_contact VARCHAR(255) AFTER address_reference;
