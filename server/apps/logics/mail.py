#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-29 19:46:56
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     邮箱业务接口
# @end
# @copyright (C) 2015, kimech

from apps.configs.msg_code import MsgCode

from apps.services.mail import MailService
from apps.logics import package as pack_logic

from .helpers import common_helper

MAIL_STATE_NEW = 0
MAIL_STATE_READ = 1
MAIL_STATE_GOT = 2

# ========================= GAME API ==============================
def info(context):
    """读取邮箱数据

    Args:

    Returns:

    """
    ki_user = context.user

    new_mails, read_mails = MailService.get_user_mails(ki_user.uid)

    data = {}
    data["new_mails"] = new_mails
    data["read_mails"] = read_mails

    context.result["data"] = data

def read(context):
    """阅读邮件内容

    Args:
        mail_id 邮件ID

    Returns:
        mc
    """
    ki_user = context.user

    mail_id = context.get_parameter("mail_id")

    state = MailService.check_mail_state(ki_user.uid, mail_id)

    if state is None:
        context.result['mc'] = MsgCode['MailNotExist']
        return
    elif state != MAIL_STATE_NEW:
        context.result['mc'] = MsgCode['MailAlreadyRead']
        return
    else:
        pass

    MailService.update_mail_state(ki_user.uid, mail_id, MAIL_STATE_READ)

    context.result["mc"] = MsgCode["MailReadSucc"]

def get_attachments(context):
    """收取附件

    Args:
        mail_ids 收取附件的邮件ID列表 []

    Returns:
        mc
    """
    ki_user = context.user

    mail_ids = context.get_parameter("mail_ids", "[]")
    try:
        mail_ids = eval(mail_ids)
        if (not isinstance(mail_ids, list)) or (len(mail_ids) <= 0):
            raise

        mail_ids = [int(mid) for mid in mail_ids]
    except:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    items = []
    for mail_id in mail_ids:
        state = MailService.check_mail_state(ki_user.uid, mail_id)
        if state is None:
            context.result['mc'] = MsgCode['MailNotExist']
            return
        elif state == MAIL_STATE_GOT:
            context.result['mc'] = MsgCode['MailAlreadyGot']
            return
        else:
            items.append(MailService.get_attachments(ki_user.uid, mail_id))

    pack_logic.add_items(ki_user, common_helper.handle_pack_items(items))
    for mail_id in mail_ids:
        MailService.update_mail_state(ki_user.uid, mail_id, MAIL_STATE_GOT)

    context.result["mc"] = MsgCode["MailGetAttachmentsSucc"]
