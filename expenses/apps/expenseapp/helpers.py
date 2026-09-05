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
from django.template.loader import render_to_string
from PIL import Image
import tempfile
import logging

logger = logging.getLogger(__name__)

PDF_EXTENSIONS = ('.pdf',)
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.heic')


def receipt_file_type(file):
  name = file.name.lower()
  if not getattr(file, 'path', None) or not os.path.exists(file.path):
    return None

  if name.endswith(PDF_EXTENSIONS):
    try:
      with open(file.path, 'rb') as handle:
        if handle.read(5) != b'%PDF-':
          return None
        handle.seek(0)
        reader = PyPDF2.PdfReader(handle, strict=False)
        if len(reader.pages) == 0:
          return None
      return 'pdf'
    except Exception:
      logger.warning('Skipping invalid PDF receipt: %s', file.name, exc_info=True)
      return None

  if name.endswith(IMAGE_EXTENSIONS):
    try:
      with Image.open(file.path) as image:
        image.verify()
      return 'image'
    except Exception:
      logger.warning('Skipping invalid image receipt: %s', file.name, exc_info=True)
      return None

  return None

def render_to_pdf(template_src, context_dict, additional=[]):
  from weasyprint import HTML

  html_string = render_to_string(template_src, context_dict)

  html = HTML(string=html_string)
  form = io.BytesIO(html.write_pdf())

  pdf = PyPDF2.PdfMerger(strict=False)
  pdf.append(form)

  for file in additional:
    if file.name:
      file_type = receipt_file_type(file)
      if not file_type:
        continue

      filename = file.path
      if file_type == 'image':
        tmp = tempfile.NamedTemporaryFile(delete=False)
        try:
          with Image.open(filename) as im:
            if im.mode in ('RGBA', 'P'):
              im = im.convert('RGB')
#          filename = filename.replace('.jpg', '.pdf').replace('.png', '.pdf')
#          im.save(filename, "PDF", resolution=200.0)
            im.save(tmp.name, "PDF", resolution=200.0)
          with open(tmp.name, 'rb') as receipt_pdf:
            pdf.append(receipt_pdf)
        finally:
          tmp.close()
          os.unlink(tmp.name)
      else:
        with open(filename, 'rb') as receipt_pdf:
          pdf.append(receipt_pdf, import_outline=False)

  output = io.BytesIO()
  pdf.write(output)

  return HttpResponse(output.getvalue(), content_type='application/pdf')
