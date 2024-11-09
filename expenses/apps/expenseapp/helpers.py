# -*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy
import locale

# Lähde: http://www.ohjelmointiputka.net/koodivinkit/26782-python-viitenumerolaskuri


def viitenumeron_tarkiste(viitenumero_raaka):
    """palauta annetun tarkisteettoman viitenumeron perään kuuluva tarkistenumero"""
    kertoimet = (7, 3, 1)
    viitenumero_raaka = viitenumero_raaka.replace(' ', '')
    nrot_kaanteinen = list(map(int, viitenumero_raaka[::-1]))
    tulosumma = sum(kertoimet[i % 3] * x for i,
                    x in enumerate(nrot_kaanteinen))
    return (10 - (tulosumma % 10)) % 10


def decimal_in_r82(number):
    return format(number, '.2f').replace('.', ',')


def decimal_without_separator(number):
    return int(round(float(number)*100))


def cc_expense(instance):
    from django.core.mail import send_mail
    from expenseapp.models import ExpenseLine
    if instance.cc_email:
        # Send email
        lines = ExpenseLine.objects.filter(expense=instance)
        rows = gettext_lazy("Date\t\tType\t\tAmount\n")
        rowtemplate = " %s\t%s\t%s×%s=%s\n%s\n\n"
        for line in lines:
            rows = rows + rowtemplate % (line.begin_at.strftime('%d.%m.%Y'), line.expensetype,
                                         line.basis, line.multiplier, locale.currency(line.sum(), False), line.description)

        body = ("""Hi,

You were CC'd in a new expense application for %s.

Name:        %s
Description: %s

Expense lines:
 %s
Total: %s

Best regards,
-- 
Yhrek.fi
""")
# VAIHDA lähettäjä email
        send_mail(str(gettext_lazy('New expense CC\'d to you')),
                  body % (instance.organisation.name, instance.name, instance.description, str(
                      rows), str(locale.currency(instance.amount()))),
                  'info@yhrek.fi', [instance.cc_email], False)

import io, os
from django.http import HttpResponse
import PyPDF2
from weasyprint import HTML
from django.template.loader import render_to_string
from PIL import Image
import tempfile

def render_to_pdf(template_src, context_dict, additional=[]):
  html_string = render_to_string(template_src, context_dict)

  html = HTML(string=html_string)
  form = io.BytesIO(html.write_pdf())

  pdf = PyPDF2.PdfMerger(strict=False)
  pdf.append(form)

  for file in additional:
    if file.name:
      filename = file.url
      if '.jpg' in file.name.lower() or '.png' in file.name.lower() or '.jpeg' in file.name.lower():
        tmp = tempfile.NamedTemporaryFile(delete=False)
        try:
          im = Image.open(filename)
          if im.mode == 'RGBA':
            im = im.convert('RGB')
#          filename = filename.replace('.jpg', '.pdf').replace('.png', '.pdf')
#          im.save(filename, "PDF", resolution=200.0)
          im.save(tmp.name, "PDF", resolution=200.0)
          pdf.append(open(tmp.name, 'rb'))
        finally:
          tmp.close()
          os.unlink(tmp.name)
      else:
        pdf.append(open(filename, 'rb'), import_outline=False)

  output = io.BytesIO()
  pdf.write(output)

  return HttpResponse(output.getvalue(), content_type='application/pdf')
