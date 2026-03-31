#!/bin/bash
set -e
clickhouse client --verbose -n <<-EOSQL
    CREATE DATABASE IF NOT EXISTS "otel";
EOSQL
