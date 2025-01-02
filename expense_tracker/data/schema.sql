CREATE TABLE users(
    id SERIAL PRIMARY KEY,
    user_name VARCHAR(20) NOT NULL UNIQUE,
    user_password VARCHAR(60) NOT NULL
);

CREATE TABLE categories(
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

INSERT INTO categories(name)
VALUES ('Health'),
        ('Groceries'),
        ('Food & Drink'),
        ('Housing'),
        ('Utilities'),
        ('Shopping'),
        ('Travel'),
        ('Other');

CREATE TABLE expenses(
    id SERIAL PRIMARY KEY,
    transaction_datetime timestamp NOT NULL,
    amount_cents_usd INT NOT NULL,
    description TEXT NOT NULL,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    category_id INT REFERENCES categories(id) ON DELETE RESTRICT
);