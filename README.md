KimAlert
========

A CLI [Kimsufi](https://www.kimsufi.com/fr/index.xml) seeker, able to notify you via push messages

###Usage

 2. Listing all server models status 

    ```shell
    python kimalert.py
    ```

 3. Getting a specific server model status

    ```shell
    python kimalert.py -k KS-1
    ```

 4. Getting many specific server models status

    ```shell
    python kimalert.py -k KS-1,KS-3,KS-4
    ```

 5. Being alerted by a push notification (via Pushbullet)

    ```shell
    python kimalert.py -k KS-1 -t PUSHBULLET_TOKEN
    ```
