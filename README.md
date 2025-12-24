# ✂️ TrimTime: Intelligent Salon Reservation System

A multi-tenant scheduling platform connecting customers with local barbershops. The system features a dynamic reservation engine that calculates available time slots in real-time based on service duration, shop operating hours, and existing booking conflicts.

#### Video Demo:  https://youtu.be/eHhbaZaA-sc?feature=shared

## 🚀 Key Features

### 1. Dynamic Time-Slot Allocation Algorithm
Unlike standard booking apps that use fixed 30-minute blocks, TrimTime utilizes a custom **greedy scheduling algorithm** to maximize salon efficiency:
* **Real-time Calculation:** Automatically calculates the start and end time of a reservation based on the specific duration of the chosen haircut (e.g., a 45-minute cut vs. a 15-minute trim).
* **Conflict Prevention:** Queries the database for the *last allocated end-time* to ensure no overlapping bookings occur for a specific barber.
* **Edge Case Handling:** Automatically detects if a service duration exceeds the shop's closing time and intelligently suggests the next available slot on the following business day.

### 2. Role-Based Access Control (RBAC)
The application implements distinct workflows for two user types:
* **Customers:** Can browse salons, view service menus, input custom "Specialized" requests, and track reservation history.
* **Salons:** Access a management dashboard to view pending appointments, manage their service catalog (CRUD operations for Haircuts), and update operating hours.

### 3. "Specialized" Service Logic
The database schema handles polymorphic service requests:
* Users can select from a standard list of services (Foreign Key to `haircuts` table).
* Alternatively, users can submit **"Specialized Descriptions"** (custom text inputs) with estimated durations, which the system normalizes into the scheduling logic just like standard services.

### 4. Automated Status Management
* **Auto-Fulfillment:** A background check verifies if a reservation's end-time has passed and automatically updates the status from `Pending` to `Fulfilled`.
* **Cancellation Handling:** Atomic transactions ensure that when a reservation is canceled, the time slot is immediately freed up for new users.

## 🛠 Database Schema
The system runs on a relational **SQLite** database enforcing strict integrity:
* **`Users` & `Salons`:** One-to-One relationship (A user account can be upgraded to a Salon profile).
* **`Reservations`:** The central join table linking Users, Salons, and Haircuts, with cascading deletes to prevent orphaned records if a user/salon account is removed.

## 💻 Tech Stack
* **Backend:** Python (Flask)
* **Database:** SQLite3 (Native Python implementation)
* **Frontend:** Jinja2, HTML5, CSS3, Bootstrap
* **Security:** Werkzeug Security (Scrypt password hashing)

## 🔧 Local Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/Py-God/trimtime.git](https://github.com/Py-God/trimtime.git)
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Initialize the Database:**
    * Create a file named `trimtime.db`.
    * Run the schema script:
        ```bash
        sqlite3 trimtime.db < schema.sql
        ```

4.  **Run the Application:**
    ```bash
    flask run
    ```

---
*Developed by [Boluwatife Leke-Oduoye](https://github.com/Py-God)*
