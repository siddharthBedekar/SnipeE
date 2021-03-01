package com.example.snipee;


import androidx.appcompat.app.AppCompatActivity;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.util.Log;
import android.view.MotionEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.RelativeLayout;
import android.widget.Toast;

//import io.socket.client.Ack;
import org.w3c.dom.Document;

import io.socket.client.IO;
import io.socket.client.Socket;
import io.socket.emitter.Emitter;

import java.net.URISyntaxException;


public class MainActivity extends AppCompatActivity {
    private double scaleFactorX, scaleFactorY;
    private int goal_len, striker_len, puck_len;
    private Socket socket;
    private int screenBoundX, screenBoundY;

    private int desiredX, desiredY;

    //camera dimensions
    final int CAM_X = 640;
    final int CAM_Y = 480;

    //dont recall what this is for but update coordinates somehow
    private Handler updateCoordsHandler;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // remove title and make fullscreen
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
                WindowManager.LayoutParams.FLAG_FULLSCREEN);
        setContentView(R.layout.activity_main);

        this.configureScaling();
        this.socket = initSocket();
        this.attachSocketListeners();
        this.attachTouchListeners();

    }

    @Override
    protected void onStart() {
        super.onStart();
        //main menu
        this.runGame();
    }

    @Override
    protected void onStop() {
        super.onStop();
//        this.socket.disconnect(); //find appropriate place to put this!
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
    }


    //--------------------------Game Methods-------------------------
    private void runGame(){
        //Socket init
        this.socket.connect();
    }

    @SuppressLint("ClickableViewAccessibility")
    private void attachTouchListeners(){

        ImageView userStriker = findViewById(R.id.userStriker);
        userStriker.setOnTouchListener((v, event) -> {
            final int action = event.getAction();

            switch (action & MotionEvent.ACTION_MASK) {
                case MotionEvent.ACTION_DOWN: {
                    break;
                }

                case MotionEvent.ACTION_MOVE: {
                    int newX, newY;
                    int halfx = Math.round((float)this.striker_len/2);

                    newX = (int) event.getRawX();
                    newY = (int) event.getRawY();

//                    Log.d("test1", Integer.toString(newX) + ", " + Integer.toString(newY));

                    if (newX > this.screenBoundX - halfx){
                        newX = this.screenBoundX - halfx;
                    }
                    else if(newX < halfx){
                        newX = halfx;
                    }

                    if (newY > this.screenBoundY){
                        newY = this.screenBoundY;
                    }
                    else if(newY < this.screenBoundY/2 + this.striker_len){
                        newY = this.screenBoundY/2 + this.striker_len;
                    }

//                    Log.d("test2", Integer.toString(screenBoundX) + ", " + Integer.toString(screenBoundY));

                    userStriker.setX(newX - halfx);
                    userStriker.setY(newY - this.striker_len);  //want it to stay above finger
                    break;
                }
            }
            return true;
        });
    }

    //--------------------------Socket Methods-------------------------
    private Socket initSocket(){
        try {
            return IO.socket("http://192.168.0.233:5000");
        } catch (URISyntaxException e) {
            throw new RuntimeException(e);
        }
    }

    private void attachSocketListeners(){
        // Attach event listeners
        socket.on(Socket.EVENT_CONNECT, new Emitter.Listener(){
            @Override
            public void call(Object... args) {
                String s = Build.MANUFACTURER + Build.PRODUCT + "Connected";
                socket.emit("message", s);
                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        Toast.makeText(getActivity(), "Connected", Toast.LENGTH_SHORT).show();
                    }
                });
            }
        });

        socket.on(Socket.EVENT_DISCONNECT, new Emitter.Listener(){
            @Override
            public void call(Object... args) {
                //runOnUIThread use later?
                socket.emit("message", "Cell Connected!");
                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        Toast.makeText(getActivity(), "Disconnected", Toast.LENGTH_SHORT).show();
                    }
                });
            }
        });
    }

    //--------------------------Scaling Methods-------------------------
    private int scaleX( int boardX)   throws Exception{
        if (boardX > CAM_X){
            throw new Exception("Input board x out of bound.");
        }
        return (int)Math.round(boardX*this.scaleFactorX);
    }

    private int scaleY(int boardY)   throws Exception{
        if (boardY > CAM_Y){
            throw new Exception("Input board y out of bound.");
        }
        return (int)Math.round(boardY*this.scaleFactorY);
    }

    private void configureScaling(){
        //initiate bounds
        this.screenBoundX = getDisplayDimensionX();
        this.screenBoundY = getDisplayDimensionY();

        //scaling and parameters
        this.scaleFactorX = (float)this.screenBoundX/CAM_X;
        this.scaleFactorY = (float)this.screenBoundY/CAM_Y;
        this.goal_len = Math.round((float)this.screenBoundX/3);
        this.striker_len = (this.goal_len/2);
        this.puck_len = (int) Math.round(this.striker_len/1.2);

        //make goal size to scale
        ImageView semicircle_d = findViewById(R.id.down_semicircle);
        semicircle_d.getLayoutParams().width = this.goal_len;
        semicircle_d.requestLayout();

        ImageView semicircle_u = findViewById(R.id.up_semicircle);
        semicircle_u.getLayoutParams().width = this.goal_len;
        semicircle_u.requestLayout();

        //make striker, and puck size to scale:
        ImageView userStriker = findViewById(R.id.userStriker);
        userStriker.getLayoutParams().height = this.striker_len;
        userStriker.getLayoutParams().width = this.striker_len;
        userStriker.requestLayout(); //apply the above changes to layout

        ImageView opponentStriker = findViewById(R.id.opponentStriker);
        opponentStriker.getLayoutParams().height = this.striker_len;
        opponentStriker.getLayoutParams().width = this.striker_len;
        opponentStriker.requestLayout();

        ImageView robotStriker = findViewById(R.id.robotStriker);
        robotStriker.getLayoutParams().height = this.striker_len;
        robotStriker.getLayoutParams().width = this.striker_len;
        robotStriker.requestLayout();

        ImageView puck = findViewById(R.id.puck);
        puck.getLayoutParams().height = this.puck_len;
        puck.getLayoutParams().width = this.puck_len;
        puck.requestLayout();

    }


    //--------------------------Getters and Setters-------------------------
    public Activity getActivity(){
        return this;
    }

    private int getDisplayDimensionX(){
        return getResources().getDisplayMetrics().widthPixels;
    }

    private int getDisplayDimensionY(){
        return getResources().getDisplayMetrics().heightPixels;
    }

}

