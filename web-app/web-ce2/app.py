import os
import boto3
import socket
from flask import Flask, render_template_string, request, session, redirect, url_for

app = Flask(__name__)
# זה השלב הקריטי - בלי זה ה-Session לא עובד וגורם לשגיאה 500
app.secret_key = "aws-resource-viewer-secret-123"

def get_aws_clients():
    """מנסה ליצור חיבור ל-AWS. מחזיר None אם המפתחות לא קיימים/תקינים"""
    ak = session.get("aws_ak")
    sk = session.get("aws_sk")
    rn = session.get("aws_rn")
    
    if ak and sk and rn:
        try:
            sess = boto3.Session(
                aws_access_key_id=ak,
                aws_secret_access_key=sk,
                region_name=rn
            )
            return sess.client("ec2"), sess.client("elbv2")
        except:
            return None, None
    return None, None

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        session["aws_ak"] = request.form.get("ak", "").strip()
        session["aws_sk"] = request.form.get("sk", "").strip()
        session["aws_rn"] = request.form.get("rn", "").strip()
        return redirect(url_for("home"))

    # אתחול רשימות ריקות כדי למנוע שגיאות ב-HTML
    data = {"instances": [], "vpcs": [], "error": None}
    
    ec2, elb = get_aws_clients()

    if ec2:
        try:
            # EC2
            res = ec2.describe_instances()
            for r in res.get("Reservations", []):
                for i in r.get("Instances", []):
                    name = next((t["Value"] for t in i.get("Tags", []) if t["Key"] == "Name"), "N/A")
                    data["instances"].append({
                        "Name": name, "ID": i["InstanceId"], "State": i["State"]["Name"],
                        "Type": i["InstanceType"], "IP": i.get("PublicIpAddress", "N/A")
                    })
            # VPC
            vpcs = ec2.describe_vpcs().get("Vpcs", [])
            data["vpcs"] = [{"ID": v["VpcId"], "CIDR": v["CidrBlock"]} for v in vpcs]
        except Exception as e:
            data["error"] = f"שגיאת התחברות ל-AWS: {str(e)}"

    html = """
    <body style="font-family: sans-serif; direction: rtl; padding: 20px; background: #f4f4f4;">
        <div style="max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 10px;">
            <h2>צופה משאבי AWS</h2>
            
            {% if not session.get('aws_ak') %}
                <form method="POST" style="background: #eee; padding: 15px; border-radius: 5px;">
                    <input name="ak" placeholder="Access Key" required style="display:block; margin: 10px 0; width: 100%;">
                    <input name="sk" type="password" placeholder="Secret Key" required style="display:block; margin: 10px 0; width: 100%;">
                    <input name="rn" placeholder="Region (us-east-1)" required style="display:block; margin: 10px 0; width: 100%;">
                    <button type="submit" style="background: #27ae60; color: white; border: none; padding: 10px; width: 100%;">התחבר</button>
                </form>
            {% else %}
                <a href="/logout"><button style="float:left; background: #e74c3c; color: white; border: none; padding: 5px;">התנתק</button></a>
                <p>מחובר ל: <b>{{ session['aws_rn'] }}</b></p>
                
                {% if data.error %}<p style="color: red;">{{ data.error }}</p>{% endif %}

                <h3>אינסטנסים (EC2)</h3>
                <table border="1" style="width:100%; border-collapse: collapse;">
                    <tr style="background: #3498db; color: white;"><th>שם</th><th>סטטוס</th><th>IP</th></tr>
                    {% for i in data.instances %}
                    <tr><td>{{ i.Name }}</td><td>{{ i.State }}</td><td>{{ i.IP }}</td></tr>
                    {% endfor %}
                </table>
            {% endif %}
        </div>
    </body>
    """
    return render_template_string(html, data=data)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"\n--- השרת מוכן! ---")
    print(f"כתובת מקומית: http://localhost:5001")
    print(f"כתובת ברשת: http://{local_ip}:5001\n")
    app.run(host="0.0.0.0", port=5001)