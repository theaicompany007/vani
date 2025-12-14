-- Add contact_management and company_management use cases if they don't exist
INSERT INTO use_cases (code, name, description) 
VALUES 
  ('contact_management', 'Contact Management', 'Manage contacts and contact data'),
  ('company_management', 'Company Management', 'Manage companies and company data')
ON CONFLICT (code) DO NOTHING;
















