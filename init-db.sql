-- Initialize database for Finance Management application
CREATE DATABASE IF NOT EXISTS finance_management;
CREATE USER IF NOT EXISTS finance_user;
GRANT ALL PRIVILEGES ON DATABASE finance_management TO finance_user;