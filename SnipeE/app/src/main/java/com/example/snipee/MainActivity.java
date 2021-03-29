package com.example.snipee;


import androidx.appcompat.app.AppCompatActivity;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import android.view.MotionEvent;
import android.view.Window;
import android.view.WindowManager;
import android.widget.ImageView;
import android.widget.Toast;

import io.socket.client.IO;
import io.socket.client.Socket;

import java.net.URISyntaxException;


public class MainActivity extends AppCompatActivity {
    private float scaleFactorX, scaleFactorY;
    private int striker_len;
    private int puck_len;
    private Socket socket;
    private int screenBoundX, screenBoundY;
    private Coord_filter filter;    //moving average filter
    private Coord_Interpolator interp; //interpolator

    private int desiredX, desiredY;

    //CONSTANTS
    final int CAM_X = 640;
    final int CAM_Y = 480;
    final int FILTER_WINDOW_SIZE = 5;
    final String SERVER_URI = "http://192.168.1.48:5000";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // remove title and make fullscreen
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
                WindowManager.LayoutParams.FLAG_FULLSCREEN);
        setContentView(R.layout.activity_main);

        this.filter = new Coord_filter(FILTER_WINDOW_SIZE);
        this.interp = new Coord_Interpolator();
        this.configureScaling();
        this.socket = initSocket();
        this.attachSocketListeners();   //for server to client socket comms
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
                    int half = Math.round((float)this.striker_len/2);

                    newX = (int) event.getRawX();
                    newY = (int) event.getRawY();
//                    Log.d("test1", Integer.toString(newX) + ", " + Integer.toString(newY));

                    if (newX > this.screenBoundX - half){
                        newX = this.screenBoundX - half;
                    }
                    else if(newX < half){
                        newX = half;
                    }

                    if (newY > this.screenBoundY){
                        newY = this.screenBoundY;
                    }
                    else if(newY < this.screenBoundY/2 + this.striker_len){
                        newY = this.screenBoundY/2 + this.striker_len;
                    }
//                    Log.d("test2", Integer.toString(screenBoundX) + ", " + Integer.toString(screenBoundY));
                    this.desiredX = (newX-half);
                    this.desiredY = (newY-half);
                    userStriker.setX(newX - half);
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
            return IO.socket(SERVER_URI);
        } catch (URISyntaxException e) {
            throw new RuntimeException(e);
        }
    }

    private void attachSocketListeners(){
        // Attach event listeners for sockets

        // CONNECT EVENT----------------------------------------------------------------------------
        socket.on(Socket.EVENT_CONNECT, args -> {
            String s = Build.PRODUCT + " Connected";
            socket.emit("message", s);
            runOnUiThread(() -> Toast.makeText(getActivity(), "Connected to " + SERVER_URI,
                                                Toast.LENGTH_SHORT).show());
        });

        // PERSONAL PING TEST EVENT-----------------------------------------------------------------
        socket.on("customPing", args -> socket.emit("customPong","got it"));

        // PUCK POSITION UPDATE---------------------------------------------------------------------
        socket.on("updatePuck", args -> {
            ImageView puck = findViewById(R.id.puck);
            //split args into two strings
            String paramString = (String) args[0];
            String[] params = (paramString).split(",");

            float[] newCoords;

            //apply scaling
            newCoords = toClientScaling(Float.parseFloat(params[0]),
                                        Float.parseFloat(params[1]));

            //apply filter
            newCoords = filter.getFilteredCoords(newCoords[0],
                                                 newCoords[1]);

            //apply interpolation
            newCoords = interp.interpolate(newCoords[0],
                                           newCoords[1]);

            puck.setX(newCoords[0]-((float)puck_len/2));
            puck.setY(newCoords[1]-((float)puck_len/2));
        });

        // ROBOT STRIKER POSITION UPDATE------------------------------------------------------------
        socket.on("updateRobot", args ->{
            //send desired robot striker location
            float[] scaledDesired = toServerScaling(this.desiredX, this.desiredY);
            socket.emit("desiredStrikerLocation", scaledDesired[0] +
                                                        "," + scaledDesired[1]);

            //receive new robot striker location
            ImageView robotStriker = findViewById(R.id.robotStriker);
            //split args into two strings
            String paramString = (String) args[0];
            String[] params = (paramString).split(",");

            float[] newCoords;

            //apply scaling
            newCoords = toClientScaling(Float.parseFloat(params[0]),
                    Float.parseFloat(params[1]));

            //apply filter
            newCoords = filter.getFilteredCoords(newCoords[0],
                    newCoords[1]);

            //apply interpolation
            newCoords = interp.interpolate(newCoords[0],
                    newCoords[1]);

            robotStriker.setX(newCoords[0]-((float)striker_len/2));
            robotStriker.setY(newCoords[1]-((float)striker_len/2));
        });

        // HUMAN STRIKER POSITION UPDATE------------------------------------------------------------
        socket.on("updateHuman", args ->{
            ImageView humanStriker = findViewById(R.id.userStriker);
            //split args into two strings
            String paramString = (String) args[0];
            String[] params = (paramString).split(",");

            float[] newCoords;

            //apply scaling
            newCoords = toClientScaling(Float.parseFloat(params[0]),
                    Float.parseFloat(params[1]));

            //apply filter
            newCoords = filter.getFilteredCoords(newCoords[0],
                    newCoords[1]);

            //apply interpolation
            newCoords = interp.interpolate(newCoords[0],
                    newCoords[1]);

            humanStriker.setX(newCoords[0]-((float)striker_len/2));
            humanStriker.setY(newCoords[1]-((float)striker_len/2));
        });

        // DISCONNECT EVENT-------------------------------------------------------------------------
        socket.on(Socket.EVENT_DISCONNECT, args -> {
            String s = Build.PRODUCT + " Disconnected";
            socket.emit("message", s);
            runOnUiThread(() -> Toast.makeText(getActivity(),
                                "Disconnected from " + SERVER_URI,
                                Toast.LENGTH_SHORT).show());
        });
    }

    //--------------------------Scaling Methods-------------------------
    private float[] toServerScaling(float clientX, float clientY){
        //scale to server coordinates
        float[] result = new float[2];

        // change orientation
        result[0] = clientY/this.scaleFactorY;
        result[1] = (int) Math.round(clientX/this.scaleFactorX);
        return result;
    }

    private float[] toClientScaling(float serverX, float serverY){
        //scale to client coordinates
        float[] result = new float[2];

        //change orientation
        //subtract to make origin top left for mobile client
        result[0] =  this.screenBoundX - serverY*this.scaleFactorX;
        result[1] = serverX*this.scaleFactorY;
        return result;
    }

    private void configureScaling(){
        //initiate bounds
        this.screenBoundX = getDisplayDimensionX();
        this.screenBoundY = getDisplayDimensionY();

        //scaling and parameters
        this.scaleFactorX = (float)this.screenBoundX/CAM_Y; //rotated 90 deg
        this.scaleFactorY = (float)this.screenBoundY/CAM_X; //rotated 90 deg
//        Log.d("test", screenBoundX +" "+ screenBoundY);
        int goal_len = Math.round((float) this.screenBoundX / 3);
        this.striker_len = (goal_len /2);
        this.puck_len = (int) Math.round(this.striker_len/1.2);

        //make goal size to scale
        ImageView semicircle_d = findViewById(R.id.down_semicircle);
        semicircle_d.getLayoutParams().width = goal_len;
        semicircle_d.requestLayout();

        ImageView semicircle_u = findViewById(R.id.up_semicircle);
        semicircle_u.getLayoutParams().width = goal_len;
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

