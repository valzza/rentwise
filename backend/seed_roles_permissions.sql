-- RentWise — roles, amenities, permissions and role→permission mapping.
-- Run AFTER `alembic upgrade head` and BEFORE seed_all.sql.
-- Idempotent: safe to run multiple times.

-- ── Roles ────────────────────────────────────────────────────────────
INSERT INTO roles (name, description, created_at, updated_at) VALUES
  ('admin',    'Full platform access',           NOW(), NOW()),
  ('landlord', 'Create and manage properties',   NOW(), NOW()),
  ('tenant',   'Search and rent properties',     NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

-- ── Amenities ────────────────────────────────────────────────────────
INSERT INTO amenities (name, icon, created_at, updated_at) VALUES
  ('WiFi', 'wifi', NOW(), NOW()), ('Parking', 'car', NOW(), NOW()),
  ('Air Conditioning', 'wind', NOW(), NOW()), ('Gym', 'dumbbell', NOW(), NOW()),
  ('Pool', 'droplet', NOW(), NOW()), ('Balcony', 'home', NOW(), NOW()),
  ('Dishwasher', 'layers', NOW(), NOW()), ('Washing Machine', 'rotate-cw', NOW(), NOW()),
  ('Elevator', 'arrow-up', NOW(), NOW()), ('Security', 'shield', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

-- ── Permissions ──────────────────────────────────────────────────────
INSERT INTO permissions (name, description, created_at, updated_at) VALUES
  ('property:create', 'Create property listings',        NOW(), NOW()),
  ('property:update', 'Edit property listings',          NOW(), NOW()),
  ('property:delete', 'Delete property listings',        NOW(), NOW()),
  ('booking:manage',  'Confirm or reject viewings',      NOW(), NOW()),
  ('application:manage', 'Accept or reject applications', NOW(), NOW()),
  ('lease:manage',    'Create and manage leases',        NOW(), NOW()),
  ('payment:create',  'Make payments',                   NOW(), NOW()),
  ('maintenance:manage', 'Resolve maintenance requests', NOW(), NOW()),
  ('user:manage',     'Manage user accounts',            NOW(), NOW()),
  ('settings:manage', 'Edit platform settings (CMS)',    NOW(), NOW()),
  ('audit:read',      'View the audit trail',            NOW(), NOW()),
  ('report:read',     'View platform reports',           NOW(), NOW()),
  ('data:export',     'Export data sets',                NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

-- ── Admin gets every permission ──────────────────────────────────────
INSERT INTO role_permissions (role_id, permission_id, created_at, updated_at)
SELECT r.id, p.id, NOW(), NOW()
FROM roles r CROSS JOIN permissions p
WHERE r.name = 'admin'
  AND NOT EXISTS (SELECT 1 FROM role_permissions rp WHERE rp.role_id = r.id AND rp.permission_id = p.id);

-- ── Landlord permissions ─────────────────────────────────────────────
INSERT INTO role_permissions (role_id, permission_id, created_at, updated_at)
SELECT r.id, p.id, NOW(), NOW()
FROM roles r JOIN permissions p ON p.name IN (
  'property:create','property:update','property:delete',
  'booking:manage','application:manage','lease:manage','maintenance:manage'
)
WHERE r.name = 'landlord'
  AND NOT EXISTS (SELECT 1 FROM role_permissions rp WHERE rp.role_id = r.id AND rp.permission_id = p.id);

-- ── Tenant permissions ───────────────────────────────────────────────
INSERT INTO role_permissions (role_id, permission_id, created_at, updated_at)
SELECT r.id, p.id, NOW(), NOW()
FROM roles r JOIN permissions p ON p.name IN ('payment:create')
WHERE r.name = 'tenant'
  AND NOT EXISTS (SELECT 1 FROM role_permissions rp WHERE rp.role_id = r.id AND rp.permission_id = p.id);

-- ── CMS / platform settings (static homepage content) ────────────────
INSERT INTO settings (key, value, description, created_at, updated_at) VALUES
  ('homepage_title',   'Find your next home with RentWise', 'Hero heading on the landing page', NOW(), NOW()),
  ('homepage_slogan',  'Smart rentals, powered by data',    'Hero subheading on the landing page', NOW(), NOW()),
  ('welcome_message',  'Browse thousands of verified listings and book viewings in minutes.', 'Intro paragraph on the landing page', NOW(), NOW())
ON CONFLICT (key) DO NOTHING;