import yagmail

receiver = "mahmood.alwash@yahoo.com"
body = "See attached"
# filename = "./Plots/UAL_07-05-2020 18-58-32.pdf"
# yag = yagmail.SMTP("mhokie.dev@gmail.com")
# yag.send(
#     to=receiver,
#     subject="Stock Price Buy/Sell Signal",
#     contents=body,
#     # attachments=filename,
# )

yag = yagmail.SMTP("mhokie.dev@gmail.com", oauth2_file="~/oauth2_creds.json")
yag.send(subject="Great!")