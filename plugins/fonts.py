from helper.utils import auth_filter
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from helper.helper_func import flbl, ftext

class Fonts:
    NORMAL = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

    @staticmethod
    def transform(text, mapping):
        table = str.maketrans(Fonts.NORMAL, mapping)
        return text.translate(table)

    typewriter = lambda t: Fonts.transform(t, "\U0001D670\U0001D671\U0001D672\U0001D673\U0001D674\U0001D675\U0001D676\U0001D677\U0001D678\U0001D679\U0001D67A\U0001D67B\U0001D67C\U0001D67D\U0001D67E\U0001D67F\U0001D680\U0001D681\U0001D682\U0001D683\U0001D684\U0001D685\U0001D686\U0001D687\U0001D688\U0001D689\U0001D68A\U0001D68B\U0001D68C\U0001D68D\U0001D68E\U0001D68F\U0001D690\U0001D691\U0001D692\U0001D693\U0001D694\U0001D695\U0001D696\U0001D697\U0001D698\U0001D699\U0001D69A\U0001D69B\U0001D69C\U0001D69D\U0001D69E\U0001D69F\U0001D6A0\U0001D6A1\U0001D6A2\U0001D6A3\U0001D7F6\U0001D7F7\U0001D7F8\U0001D7F9\U0001D7FA\U0001D7FB\U0001D7FC\U0001D7FD\U0001D7FE\U0001D7FF")
    outline = lambda t: Fonts.transform(t, "\U0001D538\U0001D539\u2102\U0001D53B\U0001D53C\U0001D53D\U0001D53E\u210D\u2119\U0001D541\U0001D542\U0001D543\U0001D544\u2115\U0001D546\u2119\u211A\u211D\U0001D54A\U0001D54B\U0001D54C\U0001D54D\U0001D54E\U0001D54F\U0001D550\u2124\U0001D552\U0001D553\U0001D554\U0001D555\U0001D556\U0001D557\U0001D558\U0001D559\U0001D55A\U0001D55B\U0001D55C\U0001D55D\U0001D55E\U0001D55F\U0001D560\U0001D561\U0001D562\U0001D563\U0001D564\U0001D565\U0001D566\U0001D567\U0001D568\U0001D569\U0001D56A\U0001D56B\U0001D7D8\U0001D7D9\U0001D7DA\U0001D7DB\U0001D7DC\U0001D7DD\U0001D7DE\U0001D7DF\U0001D7E0\U0001D7E1")
    serif = lambda t: Fonts.transform(t, "\U0001D400\U0001D401\U0001D402\U0001D403\U0001D404\U0001D405\U0001D406\U0001D407\U0001D408\U0001D409\U0001D40A\U0001D40B\U0001D40C\U0001D40D\U0001D40E\U0001D40F\U0001D410\U0001D411\U0001D412\U0001D413\U0001D414\U0001D415\U0001D416\U0001D417\U0001D418\U0001D419\U0001D41A\U0001D41B\U0001D41C\U0001D41D\U0001D41E\U0001D41F\U0001D420\U0001D421\U0001D422\U0001D423\U0001D424\U0001D425\U0001D426\U0001D427\U0001D428\U0001D429\U0001D42A\U0001D42B\U0001D42C\U0001D42D\U0001D42E\U0001D42F\U0001D430\U0001D431\U0001D432\U0001D433\U0001D7CE\U0001D7CF\U0001D7D0\U0001D7D1\U0001D7D2\U0001D7D3\U0001D7D4\U0001D7D5\U0001D7D6\U0001D7D7")
    bold_cool = lambda t: Fonts.transform(t, "\U0001D468\U0001D469\U0001D46A\U0001D46B\U0001D46C\U0001D46D\U0001D46E\U0001D46F\U0001D470\U0001D471\U0001D472\U0001D473\U0001D474\U0001D475\U0001D476\U0001D477\U0001D478\U0001D479\U0001D47A\U0001D47B\U0001D47C\U0001D47D\U0001D47E\U0001D47F\U0001D480\U0001D481\U0001D482\U0001D483\U0001D484\U0001D485\U0001D486\U0001D487\U0001D488\U0001D489\U0001D48A\U0001D48B\U0001D48C\U0001D48D\U0001D48E\U0001D48F\U0001D490\U0001D491\U0001D492\U0001D493\U0001D494\U0001D495\U0001D496\U0001D497\U0001D498\U0001D499\U0001D49A\U0001D49B\U0001D7CE\U0001D7CF\U0001D7D0\U0001D7D1\U0001D7D2\U0001D7D3\U0001D7D4\U0001D7D5\U0001D7D6\U0001D7D7")
    cool = lambda t: Fonts.transform(t, "\U0001D434\U0001D435\U0001D436\U0001D437\U0001D438\U0001D439\U0001D43A\U0001D43B\U0001D43C\U0001D43D\U0001D43E\U0001D43F\U0001D440\U0001D441\U0001D442\U0001D443\U0001D444\U0001D445\U0001D446\U0001D447\U0001D448\U0001D449\U0001D44A\U0001D44B\U0001D44C\U0001D44D\U0001D44E\U0001D44F\U0001D450\U0001D451\U0001D452\U0001D453\U0001D454\u210E\U0001D456\U0001D457\U0001D458\U0001D459\U0001D45A\U0001D45B\U0001D45C\U0001D45D\U0001D45E\U0001D45F\U0001D460\U0001D461\U0001D462\U0001D463\U0001D464\U0001D465\U0001D466\U0001D467\U0001D7CE\U0001D7CF\U0001D7D0\U0001D7D1\U0001D7D2\U0001D7D3\U0001D7D4\U0001D7D5\U0001D7D6\U0001D7D7")
    small_cap = lambda t: Fonts.transform(t, "ABCDEFGHIJKLMNOPQRSTUVWXYZ\u1D00\u0299\u1D04\u1D05\u1D07\uA730\u0262\u029C\u026A\u1D0A\u1D0B\u029F\u1D0D\u0274\u1D0F\u1D18\u1D1A\u0280\uA731\u1D1B\u1D1C\u1D20\u1D21\u1D22\u028F\u1D220123456789")
    script = lambda t: Fonts.transform(t, "\U0001D49C\u212C\U0001D49E\U0001D49F\u2130\u2131\U0001D4A2\u210B\u2110\U0001D4A5\U0001D4A6\u2112\u2133\U0001D4A9\U0001D4AA\u2118\U0001D4AC\u211B\U0001D4AE\U0001D4AF\U0001D4B0\U0001D4B1\U0001D4B2\U0001D4B3\U0001D4B4\U0001D4B5\U0001D4B6\U0001D4B7\U0001D4B8\U0001D4B9\u212F\U0001D4BB\u210A\U0001D4BD\U0001D4BE\U0001D4BF\U0001D4C0\U0001D4C1\U0001D4C2\U0001D4C3\U0001D4C4\u2113\U0001D4C5\U0001D4C6\U0001D4C7\U0001D4C8\U0001D4C9\U0001D4CA\U0001D4CB\U0001D4CC\U0001D4CD\U0001D4CE\U0001D4CF\U0001D4D0\U0001D4D1\U0001D4D2\U0001D4D3\U0001D4D4\U0001D4D5\U0001D4D6\U0001D4D7\U0001D4D8\U0001D4D90123456789")
    bold_script = lambda t: Fonts.transform(t, "\U0001D4D0\U0001D4D1\U0001D4D2\U0001D4D3\U0001D4D4\U0001D4D5\U0001D4D6\U0001D4D7\U0001D4D8\U0001D4D9\U0001D4DA\U0001D4DB\U0001D4DC\U0001D4DD\U0001D4DE\U0001D4DF\U0001D4E0\U0001D4E1\U0001D4E2\U0001D4E3\U0001D4E4\U0001D4E5\U0001D4E6\U0001D4E7\U0001D4E8\U0001D4E9\U0001D4EA\U0001D4EB\U0001D4EC\U0001D4ED\U0001D4EE\U0001D4EF\U0001D4F0\U0001D4F1\U0001D4F2\U0001D4F3\U0001D4F4\U0001D4F5\U0001D4F6\U0001D4F7\U0001D4F8\U0001D4F9\U0001D4FA\U0001D4FB\U0001D4FC\U0001D4FD\U0001D4FE\U0001D4FF\U0001D500\U0001D501\U0001D502\U0001D5030123456789")
    tiny = lambda t: Fonts.transform(t, "ABCDEFGHIJKLMNOPQRSTUVWXYZ\u1D43\u1D47\u1D9C\u1D48\u1D49\u1D4B\u1D4D\u02B0\u2071\u02B2\u1D4F\u02E1\u1D50\u207F\u1D52\u1D56\u1D57\u02B3\u02E2\u1D5B\u1D5C\u1D5D\u02B7\u02E3\u02B8\u1DBB0123456789")
    comic = lambda t: Fonts.transform(t, "\u13AA\u13AC\u13AD\u13AE\u13AF\u13B0\u13B1\u13B2\u13B3\u13B4\u13B5\u13B6\u13B7\u13B8\u13B9\u13BA\u13BB\u13BC\u13BD\u13BE\u13BF\u13C0\u13C1\u13C2\u13C3\u13C4\u13C5\u13C6\u13C7\u13C8\u13C9\u13CA\u13CB\u13CC\u13CD\u13CE\u13CF\u13D0\u13D1\u13D2\u13D3\u13D4\u13D5\u13D6\u13D7\u13D8\u13D9\u13DA\u13DB\u13DC\u13DD\u13DE0123456789")
    sans = lambda t: Fonts.transform(t, "\U0001D5D4\U0001D5D5\U0001D5D6\U0001D5D7\U0001D5D8\U0001D5D9\U0001D5DA\U0001D5DB\U0001D5DC\U0001D5DD\U0001D5DE\U0001D5DF\U0001D5E0\U0001D5E1\U0001D5E2\U0001D5E3\U0001D5E4\U0001D5E5\U0001D5E6\U0001D5E7\U0001D5E8\U0001D5E9\U0001D5EA\U0001D5EB\U0001D5EC\U0001D5ED\U0001D5EE\U0001D5EF\U0001D5F0\U0001D5F1\U0001D5F2\U0001D5F3\U0001D5F4\U0001D5F5\U0001D5F6\U0001D5F7\U0001D5F8\U0001D5F9\U0001D5FA\U0001D5FB\U0001D5FC\U0001D5FD\U0001D5FE\U0001D5FF\U0001D600\U0001D601\U0001D602\U0001D603\U0001D604\U0001D605\U0001D606\U0001D607\U0001D7EC\U0001D7ED\U0001D7EE\U0001D7EF\U0001D7F0\U0001D7F1\U0001D7F2\U0001D7F3\U0001D7F4\U0001D7F5")
    slant_sans = lambda t: Fonts.transform(t, "\U0001D608\U0001D609\U0001D60A\U0001D60B\U0001D60C\U0001D60D\U0001D60E\U0001D60F\U0001D610\U0001D611\U0001D612\U0001D613\U0001D614\U0001D615\U0001D616\U0001D617\U0001D618\U0001D619\U0001D61A\U0001D61B\U0001D61C\U0001D61D\U0001D61E\U0001D61F\U0001D620\U0001D621\U0001D622\U0001D623\U0001D624\U0001D625\U0001D626\U0001D627\U0001D628\U0001D629\U0001D62A\U0001D62B\U0001D62C\U0001D62D\U0001D62E\U0001D62F\U0001D630\U0001D631\U0001D632\U0001D633\U0001D634\U0001D635\U0001D636\U0001D637\U0001D638\U0001D639\U0001D63A\U0001D63B\U0001D7EC\U0001D7ED\U0001D7EE\U0001D7EF\U0001D7F0\U0001D7F1\U0001D7F2\U0001D7F3\U0001D7F4\U0001D7F5")
    slant = lambda t: Fonts.transform(t, "\U0001D63C\U0001D63D\U0001D63E\U0001D63F\U0001D640\U0001D641\U0001D642\U0001D643\U0001D644\U0001D645\U0001D646\U0001D647\U0001D648\U0001D649\U0001D64A\U0001D64B\U0001D64C\U0001D64D\U0001D64E\U0001D64F\U0001D650\U0001D651\U0001D652\U0001D653\U0001D654\U0001D655\U0001D656\U0001D657\U0001D658\U0001D659\U0001D65A\U0001D65B\U0001D65C\U0001D65D\U0001D65E\U0001D65F\U0001D660\U0001D661\U0001D662\U0001D663\U0001D664\U0001D665\U0001D666\U0001D667\U0001D668\U0001D669\U0001D66A\U0001D66B\U0001D66C\U0001D66D\U0001D66E\U0001D66F\U0001D7EC\U0001D7ED\U0001D7EE\U0001D7EF\U0001D7F0\U0001D7F1\U0001D7F2\U0001D7F3\U0001D7F4\U0001D7F5")
    sim = lambda t: Fonts.transform(t, "\U0001D5A0\U0001D5A1\U0001D5A2\U0001D5A3\U0001D5A4\U0001D5A5\U0001D5A6\U0001D5A7\U0001D5A8\U0001D5A9\U0001D5AA\U0001D5AB\U0001D5AC\U0001D5AD\U0001D5AE\U0001D5AF\U0001D5B0\U0001D5B1\U0001D5B2\U0001D5B3\U0001D5B4\U0001D5B5\U0001D5B6\U0001D5B7\U0001D5B8\U0001D5B9\U0001D5BA\U0001D5BB\U0001D5BC\U0001D5BD\U0001D5BE\U0001D5BF\U0001D5C0\U0001D5C1\U0001D5C2\U0001D5C3\U0001D5C4\U0001D5C5\U0001D5C6\U0001D5C7\U0001D5C8\U0001D5C9\U0001D5CA\U0001D5CB\U0001D5CC\U0001D5CD\U0001D5CE\U0001D5CF\U0001D5D0\U0001D5D1\U0001D5D2\U0001D5D3\U0001D7E2\U0001D7E3\U0001D7E4\U0001D7E5\U0001D7E6\U0001D7E7\U0001D7E8\U0001D7E9\U0001D7EA\U0001D7EB")
    circles = lambda t: Fonts.transform(t, "\u24B6\u24B7\u24B8\u24B9\u24BA\u24BB\u24BC\u24BD\u24BE\u24BF\u24C0\u24C1\u24C2\u24C3\u24C4\u24C5\u24C6\u24C7\u24C8\u24C9\u24CA\u24CB\u24CC\u24CD\u24CE\u24CF\u24D0\u24D1\u24D2\u24D3\u24D4\u24D5\u24D6\u24D7\u24D8\u24D9\u24DA\u24DB\u24DC\u24DD\u24DE\u24DF\u24E0\u24E1\u24E2\u24E3\u24E4\u24E5\u24E6\u24E7\u24E8\u24E9\u24EA\u2460\u2461\u2462\u2463\u2464\u2465\u2466\u2467\u2468")
    circle_dark = lambda t: Fonts.transform(t, "\U0001F150\U0001F151\U0001F152\U0001F153\U0001F154\U0001F155\U0001F156\U0001F157\U0001F158\U0001F159\U0001F15A\U0001F15B\U0001F15C\U0001F15D\U0001F15E\U0001F15F\U0001F160\U0001F161\U0001F162\U0001F163\U0001F164\U0001F165\U0001F166\U0001F167\U0001F168\U0001F169\U0001F150\U0001F151\U0001F152\U0001F153\U0001F154\U0001F155\U0001F156\U0001F157\U0001F158\U0001F159\U0001F15A\U0001F15B\U0001F15C\U0001F15D\U0001F15E\U0001F15F\U0001F160\U0001F161\U0001F162\U0001F163\U0001F164\U0001F165\U0001F166\U0001F167\U0001F168\U0001F169\u24FF\u278A\u278B\u278C\u278D\u278E\u278F\u2790\u2791\u2792")
    gothic = lambda t: Fonts.transform(t, "\U0001D504\U0001D505\u212D\U0001D507\U0001D508\U0001D509\U0001D50A\u210C\u2111\U0001D50D\U0001D50E\U0001D50F\U0001D510\U0001D511\U0001D512\u211C\U0001D514\U0001D516\U0001D517\U0001D518\U0001D519\U0001D51A\U0001D51B\U0001D51C\U0001D51E\U0001D51F\U0001D520\U0001D521\U0001D522\U0001D523\U0001D524\U0001D525\U0001D526\U0001D527\U0001D528\U0001D529\U0001D52A\U0001D52B\U0001D52C\U0001D52D\U0001D52E\U0001D52F\U0001D530\U0001D531\U0001D532\U0001D533\U0001D534\U0001D535\U0001D536\U0001D537𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗")
    gothic_bolt = lambda t: Fonts.transform(t, "\U0001D538\U0001D539\U0001D53A\U0001D53B\U0001D53C\U0001D53D\U0001D53E\U0001D53F\U0001D540\U0001D541\U0001D542\U0001D543\U0001D544\U0001D545\U0001D546\U0001D547\U0001D548\U0001D549\U0001D54A\U0001D54B\U0001D54C\U0001D54D\U0001D54E\U0001D54F\U0001D550\U0001D551\U0001D552\U0001D553\U0001D554\U0001D555\U0001D556\U0001D557\U0001D558\U0001D559\U0001D55A\U0001D55B\U0001D55C\U0001D55D\U0001D55E\U0001D55F\U0001D560\U0001D561\U0001D562\U0001D563\U0001D564\U0001D565\U0001D566\U0001D567\U0001D568\U0001D569\U0001D56A\U0001D56B𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗")
    cloud = lambda t: "".join([c + "\u0361\u035c" for c in t])
    happy = lambda t: "".join([c + "\u0306\u0308" for c in t])
    sad = lambda t: "".join([c + "\u0311\u0308" for c in t])
    special = lambda t: "".join([c + " " for c in t])
    squares = lambda t: Fonts.transform(t, "\U0001F130\U0001F131\U0001F132\U0001F133\U0001F134\U0001F135\U0001F136\U0001F137\U0001F138\U0001F139\U0001F13A\U0001F13B\U0001F13C\U0001F13D\U0001F13E\U0001F13F\U0001F140\U0001F141\U0001F142\U0001F143\U0001F144\U0001F145\U0001F146\U0001F147\U0001F148\U0001F149\U0001F130\U0001F131\U0001F132\U0001F133\U0001F134\U0001F135\U0001F136\U0001F137\U0001F138\U0001F139\U0001F13A\U0001F13B\U0001F13C\U0001F13D\U0001F13E\U0001F13F\U0001F140\U0001F141\U0001F142\U0001F143\U0001F144\U0001F145\U0001F146\U0001F147\U0001F148\U0001F1490123456789")
    squares_bold = lambda t: Fonts.transform(t, "\U0001F170\U0001F171\U0001F172\U0001F173\U0001F174\U0001F175\U0001F176\U0001F177\U0001F178\U0001F179\U0001F17A\U0001F17B\U0001F17C\U0001F17D\U0001F17E\U0001F17F\U0001F180\U0001F181\U0001F182\U0001F183\U0001F184\U0001F185\U0001F186\U0001F187\U0001F188\U0001F189\U0001F170\U0001F171\U0001F172\U0001F173\U0001F174\U0001F175\U0001F176\U0001F177\U0001F178\U0001F179\U0001F17A\U0001F17B\U0001F17C\U0001F17D\U0001F17E\U0001F17F\U0001F180\U0001F181\U0001F182\U0001F183\U0001F184\U0001F185\U0001F186\U0001F187\U0001F188\U0001F1890123456789")
    andalucia = lambda t: Fonts.transform(t, "ค๒ς๔єŦﻮђเןкɭ๓ภ๏קợгรՇยงฬאץչค๒ς๔єŦﻮђเןкɭ๓ภ๏קợгรՇยงฬאץչ0123456789")
    manga = lambda t: Fonts.transform(t, "\u5344\u1003\u1004\u1005\u1006\u1007\u1008\u1009\u100A\u100B\u100C\u100D\u100E\u100F\u1010\u1011\u1012\u1013\u1014\u1015\u1016\u1017\u1018\u1019\u101A\u101B\u101C\u101D\u101E\u101F\u1020\u1021\u1022\u1023\u1024\u1025\u1026\u1027\u1028\u1029\u102A\u102B\u102C\u102D\u102E\u102F\u1030\u1031\u1032\u1033\u1034\u10350123456789")
    stinky = lambda t: "".join([c + "\u035b" for c in t])
    bubbles = lambda t: "".join([c + "\u0366" for c in t])
    underline = lambda t: "".join([c + "\u035f" for c in t])
    ladybug = lambda t: "".join([c + "🐞" for c in t])
    rays = lambda t: "".join([c + "\u0482" for c in t])
    birds = lambda t: "".join([c + "\u0488" for c in t])
    slash = lambda t: "".join([c + "\u0338" for c in t])
    stop = lambda t: "".join([c + "\u20e0" for c in t])
    skyline = lambda t: "".join([c + "\u0346\u033b" for c in t])
    arrows = lambda t: "".join([c + "\u034e" for c in t])
    qvnes = lambda t: Fonts.transform(t, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
    strike = lambda t: "".join([c + "\u0336" for c in t])
    frozen = lambda t: "".join([c + "\u0359" for c in t])

@Client.on_message(filters.command(["font", "fonts"]) & auth_filter)
async def style_buttons(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        if not await client.mongodb.present_user(message.from_user.id):
            return await message.reply(ftext("Please /start the bot first in PM."))

    if len(message.command) < 2:
        await message.reply("Provide some text to style")
        return

    text = message.text.split(None, 1)[1]
    buttons = [
        [
            InlineKeyboardButton(text="𝚃𝚢𝚙𝚎𝚠𝚛𝚒𝚝𝚎𝚛", callback_data="style+typewriter"),
            InlineKeyboardButton(text="𝕆𝕦𝕥𝕝𝕚𝕟𝕖", callback_data="style+outline"),
            InlineKeyboardButton(text="𝐒𝐞𝐫𝐢𝐟", callback_data="style+serif"),
        ],
        [
            InlineKeyboardButton(text="𝑺𝒆𝒓𝒊𝒇", callback_data="style+bold_cool"),
            InlineKeyboardButton(text="𝑆𝑒𝑟𝑖𝑓", callback_data="style+cool"),
            InlineKeyboardButton(text="Sᴍᴀʟʟ Cᴀᴘs", callback_data="style+small_cap"),
        ],
        [
            InlineKeyboardButton(text="𝓈𝒸𝓇𝒾𝓅𝓉", callback_data="style+script"),
            InlineKeyboardButton(text="𝓼𝓬𝓻𝓲𝓹𝓽", callback_data="style+bold_script"),
            InlineKeyboardButton(text="ᵗⁱⁿʸ", callback_data="style+tiny"),
        ],
        [
            InlineKeyboardButton(text="ᑕOᗰIᑕ", callback_data="style+comic"),
            InlineKeyboardButton(text="𝗦𝗮𝗻𝘀", callback_data="style+sans"),
            InlineKeyboardButton(text="𝙎𝙖𝙣𝙨", callback_data="style+slant_sans"),
        ],
        [
            InlineKeyboardButton(text="𝘚𝘢𝘯𝘴", callback_data="style+slant"),
            InlineKeyboardButton(text="𝖲𝖺𝗇𝗌", callback_data="style+sim"),
            InlineKeyboardButton(text="Ⓒ︎Ⓘ︎Ⓡ︎Ⓒ︎Ⓛ︎Ⓔ︎Ⓢ︎", callback_data="style+circles"),
        ],
        [
            InlineKeyboardButton(text="🅒︎🅘︎🅡︎🅒_🅛︎🅔︎🅢︎", callback_data="style+circle_dark"),
            InlineKeyboardButton(text="𝔊𝔬𝔱𝔥𝔦𝔠", callback_data="style+gothic"),
            InlineKeyboardButton(text="𝕲𝖔𝖙𝖍𝖎𝖈", callback_data="style+gothic_bolt"),
        ],
        [
            InlineKeyboardButton(text="C͜͡l͜͡o͜͡u͜͡d͜͡s͜͡", callback_data="style+cloud"),
            InlineKeyboardButton(text="H̆̈ă̈p̆̈p̆̈y̆̈", callback_data="style+happy"),
            InlineKeyboardButton(text="S̑̈ȃ̈d̑̈", callback_data="style+sad"),
        ],
        [
            InlineKeyboardButton(flbl("Close"), callback_data="close"),
            InlineKeyboardButton(flbl("Next »"), callback_data="nxt")
        ],
    ]
    await message.reply(f"<code>{text}</code>", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^nxt$"))
async def nxt_callback(client: Client, callback: CallbackQuery):
    buttons = [
        [
            InlineKeyboardButton(text="🇸 🇵 🇪 🇨 🇮 🇦 🇱 ", callback_data="style+special"),
            InlineKeyboardButton(text="🅂🅀🅄🄰🅁🄴🅂", callback_data="style+squares"),
            InlineKeyboardButton(text="🆂︎🆀︎🆄︎🅰︎🆁︎🅴︎🆂︎", callback_data="style+squares_bold"),
        ],
        [
            InlineKeyboardButton(text="ꪖꪀᦔꪖꪶꪊᥴ𝓲ꪖ", callback_data="style+andalucia"),
            InlineKeyboardButton(text="爪卂几ᘜ卂", callback_data="style+manga"),
            InlineKeyboardButton(text="S̾t̾i̾n̾k̾y̾", callback_data="style+stinky"),
        ],
        [
            InlineKeyboardButton(text="B̥ͦu̥ͦb̥ͦbtext", callback_data="style+bubbles"),
            InlineKeyboardButton(text="U͟n͟d͟e͟r͟l͟i͟n͟e͟", callback_data="style+underline"),
            InlineKeyboardButton(text="꒒ꍏꀷꌩꌃꀎꁅ", callback_data="style+ladybug"),
        ],
        [
            InlineKeyboardButton(text="R҉a҉y҉s҉", callback_data="style+rays"),
            InlineKeyboardButton(text="B҈i҈r҈d҈s҈", callback_data="style+birds"),
            InlineKeyboardButton(text="S̸l̸a̸s̸h̸", callback_data="style+slash"),
        ],
        [
            InlineKeyboardButton(text="s⃠t⃠o⃠p⃠", callback_data="style+stop"),
            InlineKeyboardButton(text="S̺͆k̺͆y̺͆l̺͆i̺͆n̺͆e̺͆", callback_data="style+skyline"),
            InlineKeyboardButton(text="A͎r͎r͎o͎w͎s͎", callback_data="style+arrows"),
        ],
        [
            InlineKeyboardButton(text="ዪሀክቿነ", callback_data="style+qvnes"),
            InlineKeyboardButton(text="S̶t̶r̶i̶k̶e̶", callback_data="style+strike"),
            InlineKeyboardButton(text="F༙r༙o༙z༙e༙n༙", callback_data="style+frozen"),
        ],
        [
            InlineKeyboardButton(flbl("Close"), callback_data="close"),
            InlineKeyboardButton(flbl("Back"), callback_data="back_fonts")
        ],
    ]
    await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))
    await callback.answer()

@Client.on_callback_query(filters.regex("^back_fonts$"))
async def back_fonts_callback(client: Client, callback: CallbackQuery):
    buttons = [
        [
            InlineKeyboardButton(text="𝚃𝚢𝚙𝚎𝚠𝚛𝚒𝚝𝚎𝚛", callback_data="style+typewriter"),
            InlineKeyboardButton(text="𝕆𝕦𝕥𝕝𝕚𝕟𝕖", callback_data="style+outline"),
            InlineKeyboardButton(text="𝐒𝐞𝐫𝐢𝐟", callback_data="style+serif"),
        ],
        [
            InlineKeyboardButton(text="𝑺𝒆𝒓𝒊𝒇", callback_data="style+bold_cool"),
            InlineKeyboardButton(text="𝑆𝑒𝑟𝑖𝑓", callback_data="style+cool"),
            InlineKeyboardButton(text="Sᴍᴀʟʟ Cᴀᴘs", callback_data="style+small_cap"),
        ],
        [
            InlineKeyboardButton(text="𝓈𝒸𝓇𝒾𝓅𝓉", callback_data="style+script"),
            InlineKeyboardButton(text="𝓼𝓬𝓻𝓲𝓹𝓽", callback_data="style+bold_script"),
            InlineKeyboardButton(text="ᵗⁱⁿʸ", callback_data="style+tiny"),
        ],
        [
            InlineKeyboardButton(text="ᑕOᗰIᑕ", callback_data="style+comic"),
            InlineKeyboardButton(text="𝗦𝗮𝗻𝘀", callback_data="style+sans"),
            InlineKeyboardButton(text="𝙎𝙖𝙣𝙨", callback_data="style+slant_sans"),
        ],
        [
            InlineKeyboardButton(text="𝘚𝘢𝘯𝘴", callback_data="style+slant"),
            InlineKeyboardButton(text="𝖲𝖺𝗇𝗌", callback_data="style+sim"),
            InlineKeyboardButton(text="Ⓒ︎Ⓘ︎Ⓡ︎Ⓒ︎Ⓛ︎Ⓔ︎Ⓢ︎", callback_data="style+circles"),
        ],
        [
            InlineKeyboardButton(text="🅒︎🅘︎🅡︎🅒_🅛︎🅔︎🅢︎", callback_data="style+circle_dark"),
            InlineKeyboardButton(text="𝔊𝔬𝔱𝔥𝔦𝔠", callback_data="style+gothic"),
            InlineKeyboardButton(text="𝕲𝖔𝖙𝖍𝖎𝖈", callback_data="style+gothic_bolt"),
        ],
        [
            InlineKeyboardButton(text="C͜͡l͜͡o͜͡u͜͡d͜͡s͜͡", callback_data="style+cloud"),
            InlineKeyboardButton(text="H̆̈ă̈p̆̈p̆̈y̆̈", callback_data="style+happy"),
            InlineKeyboardButton(text="S̑̈ȃ̈d̑̈", callback_data="style+sad"),
        ],
        [
            InlineKeyboardButton(flbl("Close"), callback_data="close"),
            InlineKeyboardButton(flbl("Next »"), callback_data="nxt")
        ],
    ]
    await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))
    await callback.answer()

@Client.on_callback_query(filters.regex(r"^style\+"))
async def style_callback(client: Client, callback: CallbackQuery):
    style = callback.data.split("+")[1]
    method = getattr(Fonts, style, None)
    if not method:
        await callback.answer("Invalid style", show_alert=True)
        return

    import re
    current_text = callback.message.text
    match = re.search(r"<code>(.*?)</code>", current_text, re.DOTALL)
    if match:
        original_text = match.group(1)
    else:
        original_text = current_text

    new_text = method(original_text)
    try:
        await callback.message.edit_text(f"<code>{new_text}</code>", reply_markup=callback.message.reply_markup)
    except Exception:
        pass
    await callback.answer()
