#######################################
#                                     #
#              OK CARBON              #
#                                     # 
#######################################
#        Alfred ve dvore  2021        #
#######################################


from tongue_twister import TongueTwister
from se import App


if __name__ == "__main__":
    # Hra s vyslovnostou / Prepis
    TongueTwister().run()

    # Stavba / Generovanie / Karaoke
    App(speech_lang="cs-CZ").run()
