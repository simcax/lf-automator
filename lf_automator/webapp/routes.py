"""Route handlers for the web dashboard."""

from lf_automator.automator.tokenpools.pools import TokenPool
from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from loguru import logger
from lf_automator.webapp.auth import check_access_key, clear_session, require_auth, set_authenticated

bp = Blueprint("main", __name__)


def get_pool_state(pool: dict) -> str:
    """Calculate the state of a token pool based on thresholds.

    Args:
        pool: Dictionary containing pool information with 'current_count' key

    Returns:
        String indicating pool state: "critical", "warning", or "normal"
    """
    current_count = pool.get("current_count", 0)

    # Define thresholds
    # Critical: 5 or fewer tokens
    # Warning: 10 or fewer tokens
    # Normal: more than 10 tokens

    if current_count <= 5:
        return "critical"
    elif current_count <= 10:
        return "warning"
    else:
        return "normal"


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Display login form and process access key submission.

    GET: Display the login form
    POST: Process access key submission and authenticate user

    Returns:
        GET: Rendered login template
        POST: Redirect to dashboard on success, or login form with error on failure
    """
    if request.method == "POST":
        # Get access key from form
        provided_key = request.form.get("access_key", "")

        # Validate access key
        if check_access_key(provided_key):
            # Set session authentication flag
            set_authenticated(True)
            # Redirect to dashboard
            return redirect(url_for("main.dashboard"))
        else:
            # Show error message
            return render_template(
                "login.html", error="Invalid access key. Please try again."
            )

    # GET request - display login form
    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
@require_auth
def logout():
    """Clear authentication session and redirect to login.

    Returns:
        Redirect to login page
    """
    clear_session()
    return redirect(url_for("main.login"))


@bp.route("/")
@require_auth
def dashboard():
    """Display the token pool dashboard.

    Fetches all token pools from the database and displays them with their
    current state (normal/warning/critical).

    Returns:
        Rendered dashboard template with pool data or error message
    """
    try:
        # Create TokenPool instance to access database methods
        token_pool = TokenPool()

        # Query database for all token pools
        pools = []
        with token_pool.db.connection:
            with token_pool.db.connection.cursor() as cursor:
                cursor.execute(
                    """SELECT pooluuid, pooldate, startcount, currentcount, poolStatus, poolPriority
                       FROM lfautomator.accessTokenPools 
                       ORDER BY poolPriority ASC"""
                )
                rows = cursor.fetchall()

                for row in rows:
                    pool_data = {
                        "pool_uuid": str(row[0]),
                        "pool_date": row[1],
                        "start_count": row[2],
                        "current_count": row[3],
                        "pool_status": row[4],
                        "pool_priority": row[5],
                    }
                    # Calculate state for each pool
                    pool_data["state"] = get_pool_state(pool_data)
                    pools.append(pool_data)

        return render_template("dashboard.html", pools=pools)

    except Exception as error:
        logger.error(f"Error loading token pools: {error}")
        return render_template(
            "dashboard.html",
            pools=[],
            error="Unable to load token pools. Please try again later.",
        )


@bp.route("/api/pools", methods=["GET"])
@require_auth
def get_pools():
    """Fetch current token pool data as JSON.

    Returns JSON array of pool objects for use by the refresh functionality.

    Returns:
        JSON response with pool data or error message
    """
    try:
        # Create TokenPool instance to access database methods
        token_pool = TokenPool()

        # Query database for all token pools
        pools = []
        with token_pool.db.connection:
            with token_pool.db.connection.cursor() as cursor:
                cursor.execute(
                    """SELECT pooluuid, pooldate, startcount, currentcount, poolStatus, poolPriority
                       FROM lfautomator.accessTokenPools 
                       ORDER BY poolPriority ASC"""
                )
                rows = cursor.fetchall()

                for row in rows:
                    pool_data = {
                        "pool_uuid": str(row[0]),
                        "pool_date": row[1].strftime("%Y-%m-%d") if row[1] else None,
                        "start_count": row[2],
                        "current_count": row[3],
                        "pool_status": row[4],
                        "pool_priority": row[5],
                    }
                    # Calculate state for each pool
                    pool_data["state"] = get_pool_state(pool_data)
                    pools.append(pool_data)

        return jsonify(pools)

    except Exception as error:
        logger.error(f"Error fetching token pools: {error}")
        return jsonify({"error": "Unable to fetch token pools"}), 500


@bp.route("/api/pools/<pool_id>/toggle-status", methods=["POST"])
@require_auth
def toggle_pool_status(pool_id):
    """Toggle a token pool's status between active and inactive.

    Args:
        pool_id: UUID of the pool to toggle

    Returns:
        JSON response with success status or error message
    """
    try:
        # Create TokenPool instance to access database methods
        token_pool = TokenPool()

        # Verify pool exists and get current status
        with token_pool.db.connection:
            with token_pool.db.connection.cursor() as cursor:
                cursor.execute(
                    """SELECT pooluuid, poolStatus 
                       FROM lfautomator.accessTokenPools 
                       WHERE pooluuid = %s""",
                    (pool_id,),
                )
                row = cursor.fetchone()

                if not row:
                    return jsonify({"error": "Pool not found"}), 404

                current_status = row[1]

                # Toggle status
                new_status = "inactive" if current_status == "active" else "active"

                # Update pool status
                cursor.execute(
                    """UPDATE lfautomator.accessTokenPools 
                       SET poolStatus = %s 
                       WHERE pooluuid = %s""",
                    (new_status, pool_id),
                )

        return jsonify(
            {
                "success": True,
                "message": f"Pool {new_status} successfully",
                "pool_id": str(pool_id),
                "previous_status": current_status,
                "new_status": new_status,
            }
        )

    except Exception as error:
        logger.error(f"Error toggling pool status {pool_id}: {error}")
        return jsonify({"error": "Unable to toggle pool status"}), 500


@bp.route("/api/pools/<pool_id>/transaction", methods=["POST"])
@require_auth
def pool_transaction(pool_id):
    """Process a deposit or withdraw transaction for a token pool.

    Args:
        pool_id: UUID of the pool to update

    Expects JSON body with:
        - transaction_type: "deposit" or "withdraw" (required)
        - count: Number of tokens to deposit/withdraw (required, positive integer)

    Returns:
        JSON response with updated pool data or error message
    """
    try:
        # Get request data
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate transaction_type
        transaction_type = data.get("transaction_type")
        if not transaction_type:
            return jsonify({"error": "transaction_type is required"}), 400

        if transaction_type not in ["deposit", "withdraw"]:
            return (
                jsonify({"error": "transaction_type must be 'deposit' or 'withdraw'"}),
                400,
            )

        # Validate count
        count = data.get("count")
        if count is None:
            return jsonify({"error": "count is required"}), 400

        try:
            count = int(count)
        except (ValueError, TypeError):
            return jsonify({"error": "count must be a valid integer"}), 400

        if count <= 0:
            return jsonify({"error": "count must be greater than 0"}), 400

        # Create TokenPool instance to access database methods
        token_pool = TokenPool()

        # Process the transaction
        with token_pool.db.connection:
            with token_pool.db.connection.cursor() as cursor:
                # Get current pool data
                cursor.execute(
                    """SELECT pooluuid, pooldate, startcount, currentcount, poolStatus, poolPriority
                       FROM lfautomator.accessTokenPools 
                       WHERE pooluuid = %s""",
                    (pool_id,),
                )
                row = cursor.fetchone()

                if not row:
                    return jsonify({"error": "Pool not found"}), 404

                current_count = row[3]

                # Calculate new count based on transaction type
                if transaction_type == "deposit":
                    new_count = current_count + count
                else:  # withdraw
                    new_count = current_count - count
                    # Prevent negative counts
                    if new_count < 0:
                        return (
                            jsonify(
                                {
                                    "error": f"Cannot withdraw {count} tokens. Only {current_count} tokens available."
                                }
                            ),
                            400,
                        )

                # Update the pool's current count
                cursor.execute(
                    """UPDATE lfautomator.accessTokenPools 
                       SET currentcount = %s 
                       WHERE pooluuid = %s""",
                    (new_count, pool_id),
                )

                # Record the transaction in history
                history_count = count if transaction_type == "deposit" else -count
                cursor.execute(
                    """INSERT INTO lfautomator.accessTokenPoolsHistory 
                       (poolUuid, accessTokenCount) 
                       VALUES (%s, %s)""",
                    (pool_id, history_count),
                )

                # Fetch updated pool data
                cursor.execute(
                    """SELECT pooluuid, pooldate, startcount, currentcount, poolStatus, poolPriority
                       FROM lfautomator.accessTokenPools 
                       WHERE pooluuid = %s""",
                    (pool_id,),
                )
                updated_row = cursor.fetchone()

                pool_data = {
                    "pool_uuid": str(updated_row[0]),
                    "pool_date": (
                        updated_row[1].strftime("%Y-%m-%d") if updated_row[1] else None
                    ),
                    "start_count": updated_row[2],
                    "current_count": updated_row[3],
                    "pool_status": updated_row[4],
                    "pool_priority": updated_row[5],
                }
                pool_data["state"] = get_pool_state(pool_data)

        return jsonify(
            {
                "success": True,
                "message": f"Successfully {transaction_type}ed {count} tokens",
                "pool": pool_data,
            }
        )

    except Exception as error:
        logger.error(f"Error processing transaction for pool {pool_id}: {error}")
        return jsonify({"error": "Unable to process transaction"}), 500


@bp.route("/api/pools", methods=["POST"])
@require_auth
def create_pool():
    """Create a new token pool.

    Expects JSON body with:
        - token_count: Number of tokens in the pool (required)
        - pool_status: Status of the pool (optional, defaults to "inactive")

    Returns:
        JSON response with created pool data or error message
    """
    try:
        # Get request data
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate token_count
        token_count = data.get("token_count")
        if token_count is None:
            return jsonify({"error": "token_count is required"}), 400

        try:
            token_count = int(token_count)
        except (ValueError, TypeError):
            return jsonify({"error": "token_count must be a valid integer"}), 400

        if token_count <= 0:
            return jsonify({"error": "token_count must be greater than 0"}), 400

        # Get optional pool_status (defaults to "inactive" to require explicit activation)
        pool_status = data.get("pool_status", "inactive")

        # Validate pool_status
        valid_statuses = ["active", "inactive", "pending"]
        if pool_status not in valid_statuses:
            return (
                jsonify(
                    {
                        "error": f"pool_status must be one of: {', '.join(valid_statuses)}"
                    }
                ),
                400,
            )

        # Create the pool
        token_pool = TokenPool()
        pool_uuid = token_pool.create_tokenpool(
            token_count=token_count, pool_status=pool_status
        )

        # Return the created pool data
        return (
            jsonify(
                {
                    "pool_uuid": str(pool_uuid),
                    "token_count": token_count,
                    "pool_status": pool_status,
                    "message": "Pool created successfully",
                }
            ),
            201,
        )

    except ValueError as error:
        logger.error(f"Validation error creating pool: {error}")
        return jsonify({"error": str(error)}), 400
    except Exception as error:
        logger.error(f"Error creating token pool: {error}")
        return jsonify({"error": "Unable to create token pool"}), 500


@bp.route("/api/pools/<pool_id>/history", methods=["GET"])
@require_auth
def get_pool_history(pool_id):
    """Get the transaction history for a token pool.

    Args:
        pool_id: UUID of the pool

    Returns:
        JSON response with history records or error message
    """
    try:
        # Create TokenPool instance to access database methods
        token_pool = TokenPool()

        # Verify pool exists
        with token_pool.db.connection:
            with token_pool.db.connection.cursor() as cursor:
                cursor.execute(
                    """SELECT pooluuid 
                       FROM lfautomator.accessTokenPools 
                       WHERE pooluuid = %s""",
                    (pool_id,),
                )
                row = cursor.fetchone()

                if not row:
                    return jsonify({"error": "Pool not found"}), 404

                # Get history records for this pool
                cursor.execute(
                    """SELECT historyUuid, changeDate, accessTokenCount
                       FROM lfautomator.accessTokenPoolsHistory 
                       WHERE poolUuid = %s 
                       ORDER BY changeDate DESC 
                       LIMIT 50""",
                    (pool_id,),
                )
                history_rows = cursor.fetchall()

                history = []
                for hist_row in history_rows:
                    history.append(
                        {
                            "history_uuid": str(hist_row[0]),
                            "change_date": (
                                hist_row[1].strftime("%Y-%m-%d %H:%M:%S")
                                if hist_row[1]
                                else None
                            ),
                            "token_count": hist_row[2],
                        }
                    )

        return jsonify({"pool_id": str(pool_id), "history": history})

    except Exception as error:
        logger.error(f"Error fetching pool history {pool_id}: {error}")
        return jsonify({"error": "Unable to fetch pool history"}), 500


@bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for liveness monitoring.

    This endpoint does not require authentication and is used by Clever Cloud
    for liveness checks.

    Returns:
        JSON response with status "ok"
    """
    return jsonify({"status": "ok"})
