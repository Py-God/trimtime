-- Users table: Stores login info for both Customers and Salons
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    is_salon TEXT NOT NULL DEFAULT 'False' -- Stored as string based on your app logic
);

-- Salons table: specific details for users who are salons
-- Note: salon_id links directly to users.id (One-to-One relationship)
CREATE TABLE salons (
    salon_id INTEGER PRIMARY KEY,
    salon_name TEXT NOT NULL UNIQUE,
    barber_number INTEGER NOT NULL,
    open_time TEXT NOT NULL,
    close_time TEXT NOT NULL,
    FOREIGN KEY(salon_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Haircuts table: Services offered by specific salons
CREATE TABLE haircuts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    salon_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    estimated_time INTEGER NOT NULL, -- In minutes
    FOREIGN KEY(salon_id) REFERENCES salons(salon_id) ON DELETE CASCADE
);

-- Reservations table: The core logic
CREATE TABLE reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    salon_id INTEGER NOT NULL,
    haircut_id INTEGER, -- Can be NULL if it is a "specialized" description
    specialized_description TEXT,
    estimated_time INTEGER NOT NULL,
    reservation_date TEXT NOT NULL, -- Format YYYY-MM-DD
    reservation_time_start TEXT NOT NULL,
    reservation_time_end TEXT NOT NULL,
    status TEXT DEFAULT 'Pending', -- Pending, Fulfilled, Canceled
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(salon_id) REFERENCES salons(salon_id) ON DELETE CASCADE,
    FOREIGN KEY(haircut_id) REFERENCES haircuts(id)
);
