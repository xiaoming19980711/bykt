# coding=gbk

from django.shortcuts import redirect
from .models import Student
from .models import Article
from .forms import LoginForm
from django.shortcuts import render
from gensim import corpora, models, similarities
from urllib.request import quote, urlopen
from lxml import etree
import jieba
import re
import numpy as np
from . import models as Models

# Create your views here.

def test(request):
    return render(request, 'main/test.html')


def index(request):
    is_login = request.session.get('is_login', None)
    return render(request, 'main/index.html', locals())


def login(request):
    if request.session.get('is_login', None):
        return redirect('/index/')

    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        message = ""
        if login_form.is_valid():
            studentID = login_form.cleaned_data['studentID']
            password = login_form.cleaned_data['password']
            try:
                student = Student.objects.get(studentID=studentID)
                if password == student.password:
                    request.session['studentID'] = student.studentID
                    request.session['id'] = student.id
                    request.session['name'] = student.name
                    request.session['is_login'] = True
                    return redirect('/index/')
                else:
                    message = "密码错误！"
            except:
                message = "学号错误！"
    login_form = LoginForm(request.POST)
    return render(request, 'main/login.html', locals())


def register(request):
    return render(request, 'main/register.html')


def logout(request):
    request.session.flush()
    return render(request, 'main/logout.html')


def cut_text(text, lenth):
    textArr = re.findall('.{'+str(lenth)+'}', text)
    textArr.append(text[(len(textArr)*lenth):])
    return textArr


def get_html(url1):
    ret1 = quote(url1, safe=";/?:@&=+$,", encoding="utf-8")
    res = urlopen(ret1)
    html = res.read().decode('utf-8')
    return html


def get_similarity_rate(all_doc, doc_test):
    p = ',.＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～?????\u3000、〃〈〉《》「」『』【】〔〕〖〗?????〝〞????–—‘’?“”??…?﹏﹑﹔·！？?。''＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～?????\u3000、〃〈〉《》「」『』【】〔〕〖〗?????〝〞????–—‘’?“”??…?﹏﹑﹔·！？?。'
    _doc_test = re.sub("[%s]+" % p, "", doc_test)
    _all_doc = [re.sub("[%s]+" % p, "", doc) for doc in all_doc]
    all_doc_list = []
    for doc in _all_doc:
        doc_list = [word for word in jieba.cut(doc)]
        all_doc_list.append(doc_list)
    doc_test_list = [word for word in jieba.cut(_doc_test)]
    dictionary = corpora.Dictionary([doc_test_list])
    corpus = [dictionary.doc2bow(doc) for doc in all_doc_list]
    doc_test_vec = dictionary.doc2bow(doc_test_list)
    tfidf = models.TfidfModel(corpus)
    index = similarities.SparseMatrixSimilarity(tfidf[corpus], num_features=len(dictionary.keys()))
    sim = index[tfidf[doc_test_vec]]
    if max(sim) < 1e-5 and _all_doc[sim.tolist().index(max(sim))] in _doc_test:
        return [doc_test, all_doc[sim.tolist().index(max(sim))],
                round(len(_all_doc[sim.tolist().index(max(sim))]) / len(_doc_test), 3)]
    return [doc_test, all_doc[sim.tolist().index(max(sim))], round(max(sim), 3)]


def article(request):
    global similarity_rates
    lines = request.GET['article_name']
    org_text = lines
    cc_text = ""
    lines = cut_text(lines, 20)
    header = "http://www.baidu.com/s?wd="
    similarity_rates = []
    for line in lines:
        if (len(line) == 0):
            continue
        html = get_html(header + line)
        et_html = etree.HTML(html)
        # match_texts = et_html.xpath("//*[@id]/div[1]/em")
        urls = et_html.xpath('//*[@id]/h3/a/@href')
        url_no = len(urls)
        match_texts = {}
        for No in range(1, url_no+1):
            matchs = et_html.xpath('//*[@id="%d"]/div[1]/em' % No)
            for m in matchs:
                match_texts[m.text] = No-1
        ems = []
        for m_txt in match_texts:
            ems.append(m_txt)
        try:
            tmp = get_similarity_rate(ems, line)
            match_em = tmp[1]
            tmp.insert(2, urls[match_texts[match_em]])
            similarity_rates.append(tmp)
        except:
            similarity_rates.append([line, str(ems), "无匹配链接", 0])
    for similarity_rate in similarity_rates:
        cc_text += similarity_rate[1]
    c, flag = lcs(org_text, cc_text)
    len_org = len(org_text)
    len_cc = len(cc_text)
    repeat_index = []

    while len_org > 0 and len_cc > 0:
        if flag[len_org][len_cc] == "up":
            len_org = len_org-1
        elif flag[len_org][len_cc] == "left":
            len_cc = len_cc-1
        elif flag[len_org][len_cc] == "ok":
            len_org = len_org - 1
            len_cc = len_cc - 1
            repeat_index.append(len_org)
    authorName = request.GET['authorname']
    articletitle = request.GET['articletitle']
    articlesim = 0.0
    for similarity_rate in similarity_rates:
        articlesim += similarity_rate[3]
    articlesim /= len(similarity_rates)

    Models.Article.objects.create(authorName=authorName, articleTitle=articletitle, articleContent=org_text, articlecopyContent=cc_text, article_copy_rate=articlesim, student_id=request.session['id'] + 1)

    context = {
        'similarity_rates': similarity_rates,
        'org_text': org_text,
        'org_index': repeat_index
    }
    return render(request, 'main/article.html', context=context)


def article_input(request):
    stuID = request.session['id'] + 1
    objs = Models.Article.objects.filter(student_id=stuID).values()
    context = {
       'objs': objs
    }
    return render(request, 'main/article_input.html', context)


def lcs(a, b):
    lena = len(a)
    lenb = len(b)
    c = [[0 for i in range(lenb+1)] for j in range(lena+1)]
    flag = [[0 for i in range(lenb+1)] for j in range(lena+1)]
    for i in range(lena):
        for j in range(lenb):
            if a[i] == b[j]:
                c[i+1][j+1] = c[i][j]+1
                flag[i+1][j+1] = "ok"
            elif c[i+1][j] > c[i][j+1]:
                c[i+1][j+1] = c[i+1][j]
                flag[i+1][j+1] = "left"
            else:
                c[i+1][j+1] = c[i][j+1]
                flag[i+1][j+1] = "up"
    return c, flag


def show_detail(request):
    id = request.GET['id']
    objs = Models.Article.objects.filter(articleID=id).values()
    org_text = objs[0]['articleContent']
    cc_text = objs[0]['articlecopyContent']
    c, flag = lcs(org_text, cc_text)
    len_org = len(org_text)
    len_cc = len(cc_text)
    repeat_index = []

    while len_org > 0 and len_cc > 0:
        if flag[len_org][len_cc] == "up":
            len_org = len_org - 1
        elif flag[len_org][len_cc] == "left":
            len_cc = len_cc - 1
        elif flag[len_org][len_cc] == "ok":
            len_org = len_org - 1
            len_cc = len_cc - 1
            repeat_index.append(len_org)
    context = {
        'org_text': org_text,
        'org_index': repeat_index
    }
    return render(request, 'main/show_detail.html', context)

