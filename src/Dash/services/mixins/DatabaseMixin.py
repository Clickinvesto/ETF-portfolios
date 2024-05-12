from flask import current_app

db = current_app.db


class DatabaseMixin:

    def execute_query(self, query_string, params_dict):
        try:
            db.session.execute(db.text(query_string), params_dict)
            db.session.commit()

            return {"status": "200", "message": "Query executed"}
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database query error: {query_string}")
            current_app.logger.error(e)
            return {
                "status": "400",
                "message": "Something went wrong",
            }
