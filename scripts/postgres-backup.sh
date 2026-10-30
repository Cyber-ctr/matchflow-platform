#!/bin/sh
set -eu

mode="${1:-backup}"
backup_dir="${BACKUP_DIR:-/backups}"
mkdir -p "$backup_dir"
umask 077

case "$mode" in
    backup)
        stamp="$(date -u +%Y%m%dT%H%M%SZ)"
        archive="$backup_dir/matchflow-$stamp.dump"
        partial="$archive.partial"
        if ! pg_dump --format=custom --no-owner --file="$partial" "$PGDATABASE"; then
            rm -f "$partial"
            echo "PostgreSQL backup failed." >&2
            exit 1
        fi
        if ! pg_restore --list "$partial" >/dev/null; then
            rm -f "$partial"
            echo "Backup archive validation failed." >&2
            exit 1
        fi
        mv "$partial" "$archive"
        find "$backup_dir" -type f -name 'matchflow-*.dump' -mtime "+${BACKUP_RETENTION_DAYS:-30}" -delete
        printf 'Backup completed: %s\n' "$archive"
        ;;
    restore-test)
        archive="${2:-}"
        if [ -z "$archive" ] || [ ! -f "$archive" ]; then
            echo "Usage: $0 restore-test <backup-archive>" >&2
            exit 2
        fi
        test_db="matchflow_restore_test_$(date -u +%Y%m%d%H%M%S)"
        cleanup() {
            dropdb --if-exists "$test_db"
        }
        trap cleanup EXIT HUP INT TERM
        createdb --template=template0 "$test_db"
        pg_restore --exit-on-error --no-owner --no-acl --dbname="$test_db" "$archive"
        table_count="$(psql --no-psqlrc --tuples-only --no-align --dbname="$test_db" \
            -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")"
        if [ "$table_count" -lt 1 ]; then
            echo "Restore completed but no public tables were found." >&2
            exit 1
        fi
        printf 'Restore test passed for %s (%s public tables).\n' "$archive" "$table_count"
        ;;
    *)
        echo "Usage: $0 {backup|restore-test <backup-archive>}" >&2
        exit 2
        ;;
esac
