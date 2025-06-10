# Module Import
from flask import Flask, redirect, url_for, render_template, request, send_file, jsonify
import io
import threading
import time
import paho.mqtt.publish as publish
import ssl
import crd
import MOdtager
from database import dbconnect
import pandas as pd

# Instantiate Connection
app = Flask(__name__)

@app.route("/")
def mainpage():
    conn = dbconnect()
    cur = conn.cursor()

    button_action = request.args.get("But")
    if button_action == "Create":
        crd.add_contact(cur, int(request.args.get("holdid")), request.args.get("holdnavn"))
        cur.close()
        conn.close()
        return render_template("CRUD.html", content="")

    if button_action == "Read":
        teams = []
        cur.execute("SELECT holdid, holdnavn FROM public.teams ORDER BY holdid DESC LIMIT 10")
        for holdid, holdnavn in cur.fetchall():
            teams.append(f'<tr><td>{holdid}</td><td>{holdnavn}</td></tr>')
        cur.close()
        conn.close()
        return render_template("CRUD.html", content="\n".join(teams))

    if button_action == "Update":
        try:
            crd.replace_contact(cur, request.args.get("holdid"), request.args.get("holdnavn"))
            cur.close()
            conn.close()
            return render_template("CRUD.html", content="", message="Hold opdateret!")
        except Exception as e:
            cur.close()
            conn.close()
            return render_template("CRUD.html", content="", error=f"Kunne ikke opdatere holdet: {str(e)}")

    if button_action == "Delete":
        crd.delete_contact(cur, request.args.get("holdid"))
        cur.close()
        conn.close()
        return render_template("CRUD.html", content="")

    cur.close()
    conn.close()
    return render_template("CRUD.html", content="")

@app.route("/walltid")
def walltid():
    conn = dbconnect()
    cur = conn.cursor()
    cur.execute("SELECT holdid, holdnavn,tid, lab1, lab2, lab3 FROM public.wallfollow ORDER BY tid ASC")
    holdliste = cur.fetchall()
    button_action = request.args.get("But")
    if button_action == "upload":
        holdid = request.args.get("holdid")
        tid = request.args.get("tid")
        print(f"Upload: {holdid=} {tid=} til Wallfollow")
        crd.add_timewall(cur, holdid, tid)
        conn.commit()

    cur.close()
    conn.close()
    return render_template("time.html", holdliste=holdliste, content=crd.generate_html_table(holdliste))

@app.route("/sumotid")
def tiden():
    conn = dbconnect()
    cur = conn.cursor()
    cur.execute("SELECT holdid, holdnavn, tid FROM public.sumo ORDER BY tid ASC")
    holdliste = cur.fetchall()
    button_action = request.args.get("But")
    if button_action == "upload":
        holdid = request.args.get("holdid")
        tid = request.args.get("tid")
        print(f"Upload: {holdid=} {tid=} til sumo")
        crd.add_timesumo(cur, holdid, tid)
        conn.commit()

    cur.close()
    conn.close()
    return render_template("sumotime.html", holdliste=holdliste, content=crd.generate_html_tablesumo(holdliste))

@app.route("/excel")
def export_all_data():
    conn = dbconnect()
    try:
        # Hent data fra public.sumo
        query_sumo = "SELECT holdid, holdnavn, tid FROM public.sumo"
        df_sumo = pd.read_sql_query(query_sumo, conn)

        # Hent data fra public.wallfollow
        query_wallfollow = "SELECT holdid, holdnavn, tid FROM public.wallfollow"
        df_wallfollow = pd.read_sql_query(query_wallfollow, conn)

        # Opret en buffer til Excel-filen i hukommelsen
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_sumo.to_excel(writer, index=False, sheet_name='Sumo Tider')
            df_wallfollow.to_excel(writer, index=False, sheet_name='Wallfollow Tider')

        output.seek(0)

        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='alle_hold_tider.xlsx')

    except Exception as e:
        return f"Der opstod en fejl under eksporten: {e}"
    finally:
        if conn:
            conn.close()

@app.route("/send_mqtt")
def send_mqtt():
    command = request.args.get("command", "start")
    timestamp = str(time.time())

    # Sæt kommando og timestamp sammen med pipe som separator
    payload = f"{command}|{timestamp}"

    try:
        publish.single(
            topic="pico/start",  # Topic du ønsker at bruge
            payload=payload,
            hostname="0cf7151b3a114f89baefcd26973c2d45.s1.eu.hivemq.cloud",
            port=8883,
            auth={
                'username': "kris789",
                'password': "Dsx82yzv"
            },
            tls=ssl.create_default_context()
        )
        return {"status": " MQTT sendt", "payload": payload}
    except Exception as e:
        return {"status": " Fejl", "error": str(e)}, 500


@app.route("/upload_labtimes", methods=["POST"])
def upload_labtimes():
    try:
        times = MOdtager.pop_lab_times()
        if times is None:
            return jsonify({"status": "error", "message": "Ikke nok lab tider gemt endnu"}), 400

        holdid = request.args.get("holdid")
        if not holdid:
            return jsonify({"status": "error", "message": "Hold ID mangler"}), 400

        conn = dbconnect()
        cur = conn.cursor()
        cur.execute("""
            UPDATE wallfollow
            SET lab1 = %s, lab2 = %s, lab3 = %s
            WHERE holdid = %s
        """, (times[0], times[1], times[2], holdid))

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "success", "uploaded": times})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/get_command")
def get_command():
    current = MOdtager.get_last_command()
    print(f"Sending command to client: {current}")  # Debug log
    return {"command": current}


if __name__ == "__main__":
    threading.Thread(target=MOdtager.mqtt_thread, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)